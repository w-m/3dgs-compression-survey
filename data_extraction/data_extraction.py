from TexSoup import TexSoup
import pandas as pd
import yaml
import os
import re
import tarfile
import io
import requests
from io import StringIO



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
            if sources_file[source]["is_csv"]:
                print("read from csv")
                continue
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
    table = table.replace('\\\\ (', '')
    table = table.replace('\\\\ T', '') # remove for new paper to avoid false linebreaks
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
        if not source in tables:
            continue
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

def read_csvs(sources_file):
    #read github csv files
    csv_tables = {}
    for source in sources_file:
        if sources_file[source]["is_csv"]:
            print("From cvs source: ", source)
            url = sources_file[source]["url"]

            # convert github url to raw url
            url = url.replace("github.com", "raw.githubusercontent.com")
            url = url.replace("/blob/", "/")
            url = url.replace("/tree/", "/")
            

            for dataset in ['DeepBlending', 'SyntheticNeRF', 'TanksAndTemples', 'MipNeRF360']:
                table = requests.get(url+'/'+dataset+'.csv').text
                # if it worked
                if table and table != '404: Not Found':
                    print('Downloaded', dataset)
                    data = StringIO(table)
                    df = pd.read_csv(data,dtype={
                        'Size [Bytes]': 'Int64',
                        'PSNR': 'string',
                        'SSIM': 'string',
                        'LPIPS': 'string',
                    })
                    filled_rows = []
            
                    # Iterate over each row in the DataFrame
                    for index, row in df.iterrows():
                        filled_row = {
                            "Method": source,
                            "Submethod": row.get("Submethod", ""),
                            "PSNR": row.get("PSNR", ""),
                            "SSIM": row.get("SSIM", ""),
                            "LPIPS": row.get("LPIPS", ""),
                            "Size [Bytes]": row.get("Size [Bytes]", pd.NA),
                            "Data Source": url,
                            "Comment": ""
                        }
                        if "#Gaussians" in df.columns:
                            filled_row["#Gaussians"] = int(row.get("#Gaussians", pd.NA))

                        filled_rows.append(filled_row)
                    
                    # Convert the list of filled rows to a DataFrame
                    filled_rows_df = pd.DataFrame(filled_rows)
                    filled_rows_df["Submethod"] = filled_rows_df["Submethod"].astype('string').replace(pd.NA, '')
                    if dataset in csv_tables:
                        csv_tables[dataset] = pd.concat([csv_tables[dataset], filled_rows_df], ignore_index=True)
                    else:
                        csv_tables[dataset] = filled_rows_df
                    if "#Gaussians" in df.columns:
                        csv_tables[dataset]['#Gaussians'] = csv_tables[dataset]['#Gaussians'].astype(pd.Int64Dtype())
    return csv_tables

def df_to_results_csv(pd_tables, sources_file, csv_tables):
    #load csv files
    result_tables = {}
    for file in os.listdir("results"):
        dataset_name = file.split(".")[0]
        result_tables[dataset_name] = pd.read_csv(
            "results/" + file,
            dtype={
                'Data Source': 'string',
                'Size [Bytes]': 'Int64',
                'PSNR': 'string',
                'SSIM': 'string',
                'LPIPS': 'string',
            }
        )
        result_tables[dataset_name]['Submethod'] = result_tables[dataset_name]['Submethod'].astype('string').replace(pd.NA, '')
        
    #copy results from csv_tables
    for dataset in csv_tables:
        #get unique method names
        unique_methods = csv_tables[dataset]["Method"].unique()
        #delete all entries for unique method names in result_tables
        row_index = result_tables[dataset][result_tables[dataset]["Method"].isin(unique_methods)].index
        result_tables[dataset] = result_tables[dataset].drop(row_index)

        #iterate through all columns and transfer values
        for i in range(len(csv_tables[dataset])):
            method = csv_tables[dataset]["Method"][i]
            submethod = csv_tables[dataset]["Submethod"][i]

            #append new entry
            result_tables[dataset] = pd.concat([result_tables[dataset], csv_tables[dataset].iloc[[i]].dropna(axis=1, how='all')], ignore_index=True)

    #copy results from pd_tables
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
                        if any(val in metric for val in ["SIZE", "STORAGE", "MEM", "MB", "Mem"]):
                            value = value.replace(" MB", "").replace("MB", "") #expect MB
                            #convert to Bytes
                            value = int(float(value) * 1024 * 1024)
                            metric = "Size [Bytes]"
                        elif metric in ["PSNR","SSIM","LPIPS"]:
                            pass
                        else:
                            continue

                        # add "Submethod" column to result_tables right after "Method" if it does not exist
                        if "Submethod" not in result_tables[dataset_name].columns:
                            result_tables[dataset_name].insert(1, "Submethod", None)

                        # change submethod to "Baseline" if empty
                        if submethod == "":
                            submethod = "Baseline"
                        
                        # row index for method and submethod
                        row_index = result_tables[dataset_name].index[
                            (result_tables[dataset_name]["Method"] == source) & 
                            (result_tables[dataset_name]["Submethod"] == submethod)
                        ]
                        if len(row_index) == 0:
                            #"Method","PSNR","SSIM","LPIPS","Size [Bytes]","Data Source","Comment"
                            print("Adding new row for ", source, " ", submethod)
                            result_tables[dataset_name].loc[len(result_tables[dataset_name])] = {"Method": source, "Submethod": submethod, "PSNR": "", "SSIM": "", "LPIPS": "", "Size [Bytes]": pd.NA, "Data Source": "", "Comment": ""}
                            row_index = result_tables[dataset_name].index[
                                (result_tables[dataset_name]["Method"] == source) & 
                                (result_tables[dataset_name]["Submethod"] == submethod)
                            ]         
                        if result_tables[dataset_name].loc[row_index, metric].values[0] == value:
                            # Value already correct
                            pass
                        else:
                            print("Updating ", dataset_name, " ", source, " ", submethod, " ", metric, " to ", value)
                            result_tables[dataset_name].loc[row_index, metric] = value
                            result_tables[dataset_name].loc[row_index, "Data Source"] = sources_file[source]["url"]

    for dataset in result_tables:
        #sort by method name
        result_tables[dataset] = result_tables[dataset].sort_values(by=["Method", "Size [Bytes]"])
        #save table to csv
        result_tables[dataset].to_csv("results/" + dataset + ".csv", index=False)

if __name__ == "__main__":
    with open("data_extraction/data_source.yaml") as stream:
        try:
            sources_file = yaml.safe_load(stream)
        except yaml.YAMLError as exc:
            print(exc)

    tables = get_tables(sources_file)
    pd_tables = tex_to_pd(tables, sources_file)
    csv_tables = read_csvs(sources_file)
    df_to_results_csv(pd_tables, sources_file, csv_tables)
