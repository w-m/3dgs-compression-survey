from TexSoup import TexSoup
import pandas as pd
import yaml
import os
import re
from urllib.request import urlopen
from zipfile import ZipFile
import tarfile
import io
import requests


dataset_names = {
    "TanksAndTemples": ["Tanks", "Temples", "Tank", "Temple"],
    "MipNeRF360": ["Mip-NeRF 360", "Mip"],
    "SyntheticNeRF": ["Synthetic NeRF", "Synthetic"],
    "DeepBlending": ["Deep Blending", "Deep", "Blending"],
}


def get_tables(sources_file, local=False):
    if not local:
        tables = {}
        for source in sources_file:
            print(source)
            url = sources_file[source]["url"]
            filename = sources_file.get(source, {}).get('filename', "main.tex")
            tables_names = sources_file[source]["table_names"]

            response = requests.get(url)
            response.raise_for_status()  # Ensure the request was successful

            # Step 2: Load the content into an in-memory file
            file_like_object = io.BytesIO(response.content)

            # Step 3: Open the .tar.gz file and extract its contents
            with tarfile.open(fileobj=file_like_object, mode='r:gz') as tar:
                for member in tar.getmembers():
                    if member.isfile():  # Check if the member is a regular file
                        if filename == member.name:
                            tex = tar.extractfile(member).read().decode('utf-8')
                            soup = TexSoup(tex)
                            all_tables = soup.find_all('table')
                            all_tables += soup.find_all('table*')
                            tables[source] = []
                            for table_name in tables_names:
                                for table in all_tables:
                                    if table_name in str(table):
                                        for tabular in table.find_all("tabular"):
                                            tables[source].append(tabular)
                            break
        return tables

            
    else:
        tables = {}
        for source in sources_file:
            url = sources_file[source]["url"]
            tables_names = sources_file[source]["table_names"]
            filename = sources_file.get(source, {}).get('filename', "main.tex")
            #table_rotated = sources_file.get(source, {}).get('table_rotated', False)

            tables[source] = []
            for folder in os.listdir("data_extraction/texfiles"):
                if url.split("/")[-1] in folder:
                    with open("data_extraction/texfiles/" + folder + "/" + filename) as file:
                        tex = file.read()

                    # extract tables from tex file
                    soup = TexSoup(tex)
                    all_tables = soup.find_all('table')
                    all_tables += soup.find_all('table*')
                    for table_name in tables_names:
                        for table in all_tables:
                            if table_name in str(table):
                                for tabular in table.find_all("tabular"):
                                    tables[source].append(tabular)

                    break
        return tables

def parse_table_to_df(table, rotated=False):
    """ Parse LaTeX table to CSV format, ignoring commands and focusing on content. """
    # Remove LaTeX commands
    #replace all "\\\\" with "NEWLINE"
    table = table.replace('\\\\', 'NEWLINE')
    table = table.replace('\\n', '')
    table = table.replace('\\hline', '')
    table = table.replace('\\toprule', '')
    table = table.replace('\\midrule', '')
    table = table.replace('\\bottomrule', '')
    table = table.replace('\\cline{2-11}', '')
    table = re.sub(r'\$\S+\$', '', table) #remove all inside $$
    table = re.sub(r'\\textbf{([^}]*)}', r'\1', table) #remove all \textbf{}
    table = re.sub(r'\\cellcolor{[^}]*}{([^}]*)}', r'\1', table) #remove all \cellcolor{}
    
    # Find the tabular environment
    rows = re.findall(r'\\begin\{tabular\}.*?\\end\{tabular\}', table, re.DOTALL)
    all_rows = []
    
    for row in table.split('NEWLINE'):

        cells = re.split(r'(?<!\\)&', row)
        clean_cells = [re.sub(r'\s+', ' ', cell.strip()) for cell in cells]
        if clean_cells:
            all_rows.append(clean_cells)

    #delete first entry of first row ("methods" entry)
    all_rows[0].pop(0)

    #expect first row to be datasets, replace with name of dataset
    for entry in all_rows[0]:
        for dataset in dataset_names:
            if any(dataset_name in entry for dataset_name in dataset_names[dataset]):
                all_rows[0][all_rows[0].index(entry)] = dataset


    #check if header is 1 or 2 rows, eg multicolumn
    if any(metric in all_rows[1] for metric in ["PSNR", "psnr", "SSIM", "ssim"]):
        #pop first entry ("methods" entry)
        all_rows[1].pop(0)
        #remove avg colums / extra columns
        removed = 0
        for i in range(len(all_rows[0])):
            if any(x in all_rows[0][i-removed] for x in ["avg", "Compression Ratio", "AVG", "Avg", "Average"]): #remove all unnecessary columns
                all_rows[0].pop(i - removed)
                removed += 1
        entries_per_dataset = (len(all_rows[1])-removed) // len(all_rows[0])
        new_header = ["Method"]
        for i in range(len(all_rows[0])):
            for j in range(entries_per_dataset):
                new_header.append(all_rows[0][i] + "_" + all_rows[1][j].upper())
        
        #replace first two rows with new header
        all_rows = [new_header] + all_rows[2:]
    elif rotated:
        print("TODO (rotated)")
        return 
    else:
        #print("TODO (not multicol)")
        return 

    #remove unneccecary rows and colums, last row if it is end of table, single entry rows
    all_rows = [x[:len(all_rows[0])] for x in all_rows if not len(x)==1]
        
    # Convert list of lists (rows) to DataFrame
    df = pd.DataFrame(all_rows[1:], columns=all_rows[0])  # Assuming first row is headers
    return df

def tex_to_pd(tables, sources_file):
    pd_tables = {}
    for source in sources_file:
        print("Source: ", source)
        for table in tables[source]:

            latex_table = str(table)
            if latex_table:
                df = parse_table_to_df(latex_table, rotated=sources_file.get(source, {}).get('table_rotated', False))
                #print(df)
                if df is None:
                    continue
                if source in pd_tables:
                    pd_tables[source] = pd.concat([pd_tables[source], df], axis=1)
                else:
                    pd_tables[source] = df
            else:
                print("Table not found.")
    return pd_tables

def df_to_results_csv(pd_tables, sources_file):
    #load csv files
    result_tables = {}
    for file in os.listdir("results"):
        dataset_name = file.split(".")[0]
        result_tables[dataset_name] = pd.read_csv("results/" + file)
        result_tables[dataset_name]['Data Source'] = result_tables[dataset_name]['Data Source'].astype('string')
        result_tables[dataset_name]['Size [Bytes]'] = result_tables[dataset_name]['Size [Bytes]'].astype('Int64')
        result_tables[dataset_name]['Submethod'] = result_tables[dataset_name]['Submethod'].astype('string').fillna('').replace('<NA>', '')

    for source in pd_tables:
        print("Source: ", source)
        #delete second "Method" column if it exists from concatenating tables
        duplicates = pd_tables[source].columns.duplicated()
        pd_tables[source] = pd_tables[source].loc[:, ~duplicates]
        #find "ours" column
        for row in range(len(pd_tables[source])):
            if "ours" in pd_tables[source]["Method"][row].lower():
                # filter out submethods, everything after "ours", "" if only "ours"
                submethod = re.search(r'(?i)ours([^}]*)', pd_tables[source]["Method"][row]).group(1)
                #iterate through all columns and transfer values
                for column in pd_tables[source].columns:
                    try:
                        dataset_name = column.split("_")[0]
                        metric = column.split("_")[1]
                    except:
                        continue
                    if dataset_name in result_tables:
                        value = pd_tables[source][column][row]
                        if metric in ["SIZE", "STORAGE"]:
                            value = value.replace(" MB", "").replace("MB", "") #expect MB
                            #convert to Bytes
                            value = int(float(value) * 1024 * 1024)
                            metric = "Size [Bytes]"
                        elif metric in ["PSNR","SSIM","LPIPS"]:
                            value = float(value)
                        else:
                            continue

                        # add "Submethod" column to result_tables right after "Method" if it does not exist
                        if "Submethod" not in result_tables[dataset_name].columns:
                            result_tables[dataset_name].insert(1, "Submethod", None)
                        
                        # row index for method and submethod
                        row_index = result_tables[dataset_name].index[
                            (result_tables[dataset_name]["Method"] == source) & 
                            (result_tables[dataset_name]["Submethod"] == submethod)
                        ]
                        if len(row_index) == 0:
                            #"Method","PSNR","SSIM","LPIPS","Size [Bytes]","Data Source","Comment"
                            result_tables[dataset_name].loc[len(result_tables[dataset_name])] = {"Method": source, "Submethod": submethod, "PSNR": None, "SSIM": None, "LPIPS": None, "Size [Bytes]": None, "Data Source": None, "Comment": None}
                            row_index = result_tables[dataset_name].index[
                                (result_tables[dataset_name]["Method"] == source) & 
                                (result_tables[dataset_name]["Submethod"] == submethod)
                            ]                       
                        result_tables[dataset_name].loc[row_index, metric] = value
                        result_tables[dataset_name].loc[row_index, "Data Source"] = sources_file[source]["url"]

    for dataset in result_tables:
        #sort by method name
        result_tables[dataset] = result_tables[dataset].sort_values(by="Method")
        #save table to csv
        result_tables[dataset].to_csv("results/" + dataset + ".csv", index=False)



if __name__ == "__main__":
    with open("data_extraction/data_source.yaml") as stream:
        try:
            sources_file = yaml.safe_load(stream)
        except yaml.YAMLError as exc:
            print(exc)

    tables = get_tables(sources_file, local=1)
    pd_tables = tex_to_pd(tables, sources_file)
    df_to_results_csv(pd_tables, sources_file)
