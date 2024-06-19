import os
import pandas as pd
import bibtexparser
from jinja2 import Environment, FileSystemLoader
import re
import json
from decimal import Decimal

dataset_order = ["TanksAndTemples", "MipNeRF360", "DeepBlending", "SyntheticNeRF"]

def get_shortnames():
    #get shortnames from bibtex
    shortnames = {}
    with open("methods.bib") as bibtex_file:
        bib_database = bibtexparser.load(bibtex_file)
        for entry in bib_database.entries:
            if "shortname" in entry:
                shortnames[entry["ID"]] = entry["shortname"]
            else:
                pass
                #shortnames[entry["ID"]] = entry["ID"]
                #print(f"Shortname not found for {entry['ID']}, using ID instead")
    return shortnames

def get_links():
    #get links from bibtex
    links = {}
    with open("methods.bib") as bibtex_file:
        bib_database = bibtexparser.load(bibtex_file)
        for entry in bib_database.entries:
            if "url" in entry:
                links[entry["ID"]] = entry["url"]
            else:
                links[entry["ID"]] = ""
                print(f"Link not found for {entry['ID']}")
    return links


def combine_tables_to_html():
    dfs = []
    shortnames = get_shortnames()

    for dataset in dataset_order:
        #read csvs
        df = pd.read_csv(f'results/{dataset}.csv', dtype={'PSNR': str, 'SSIM': str, 'LPIPS': str})
        # parse all float columns to float and keep the exact numer of decimal places
        df["PSNR"] = df["PSNR"].apply(lambda x: Decimal(x) if x != '' else None)
        df["SSIM"] = df["SSIM"].apply(lambda x: Decimal(x) if x != '' else None)
        df["LPIPS"] = df["LPIPS"].apply(lambda x: Decimal(x) if x != '' else None)


        df['Submethod'] = df['Submethod'].astype('string').fillna('').replace('<NA>', '')

        #combine Method and Submethods colum into new Method column, replace method name with shortname+submethod
        df["Shortname"] = df["Method"].apply(lambda x: shortnames[x])
        df["NewMethod"] = df["Shortname"] + df["Submethod"]
        # make Method column a link to the method summary
        #df["Method"] = f'<a class="method-name '+ df["Method"] +'" href="#' + df["Method"] + '">' + df["NewMethod"] + '</a>'
        df["Method"] = f'<a class="method-name" data-method-name="'+ df["Shortname"] +'" href="#' + df["Method"] + '">' + df["NewMethod"] + '</a>'
        df.drop(columns=["Submethod", "NewMethod"], inplace=True)
        df.set_index("Method", inplace=True)
        #remove colums "Data Source" and "Comment"
        df.drop(columns=["Data Source", "Comment", "Shortname"], inplace=True)

        #change Size [Bytes] to Size [MB] and round
        if "Size [Bytes]" in df.columns:
            df["Size [MB]"] = df["Size [Bytes]"] / 1024 / 1024
            df["Size [MB]"] = df["Size [MB]"].apply(lambda x: round(x, 1))
            df.drop(columns=["Size [Bytes]"], inplace=True)

        dfs.append((dataset, df))
    
    multi_col_df = pd.concat({name: df for name, df in dfs}, axis=1)
    multi_col_df.reset_index(inplace=True)

    #calculate ranking for each method: points for ranks in PSNR, SSIM and LPIPS and size, 
    #1/n_datensätze * sum über datensatz [ (1/3 PSNR-rank + 1/3 SSIM-rank + 1/3 LPIPS-rank) / 2 + Size-rank / 2]
    #add new ranking col right after the method name
    multi_col_df.insert(1, "Rank", 0)

    for dataset in [d for d in dataset_order if d != "SyntheticNeRF"]: # SyntheticNeRF has many missing values
        for metric in ["PSNR", "SSIM", "LPIPS", "Size [MB]"]:
            if metric == "Size [MB]":
                multi_col_df["Rank"] += multi_col_df[(dataset, metric)].rank(ascending=True)  / 2
            elif metric == "LPIPS":
                multi_col_df["Rank"] += multi_col_df[(dataset, metric)].rank(ascending=True)  / 6
            else:
                multi_col_df["Rank"] += multi_col_df[(dataset, metric)].rank(ascending=False) / 6
            
    multi_col_df["Rank"] = multi_col_df["Rank"].apply(lambda x: round(x/3, 1)) # divide by 3 datasets, round to 1 decimal

    #color the top 3 values in each column
    def add_top_3_classes(df):
        colors = ['first', 'second', 'third']
        for col in df.columns:
            try:
                float_col = df[col].astype(float)
            except ValueError:
                continue

            if any(keyword in col[1].lower() for keyword in ['size', 'lpips']) or 'rank' in col[0].lower():
                top_3 = pd.Series(float_col.unique()).nsmallest(3)
            else:
                top_3 = pd.Series(float_col.unique()).nlargest(3)
            for i, val in enumerate(top_3):
                matching_indices = float_col[float_col == val].index
                for index in matching_indices:
                    df.at[index, col] = f'<td class="{colors[i]}">{df.at[index, col]}</td>'
                
        return df
    
    multi_col_df = add_top_3_classes(multi_col_df)

    html_string = multi_col_df.to_html(na_rep='', index=False, table_id="results", classes=["display", "cell-border"], 
                                      justify="center", border=0, escape=False)

    # Function to clean up nested <td> elements using regex
    def clean_nested_td(html):
        pattern = re.compile(r'<td><td([^>]*)>([^<]*)<\/td><\/td>')
        cleaned_html = pattern.sub(r'<td\1>\2</td>', html)
        return cleaned_html

    # Clean the HTML string
    cleaned_html_string = clean_nested_td(html_string)

    return cleaned_html_string

def load_methods_summaries():
    # Load the summaries of the methods
    summaries = []
    links = get_links()
    files = sorted(os.listdir('methods'))
    for file in files:
        with open(f'methods/{file}', 'r') as f:
            file_content = f.read()
            # markdown files, extarct title and summary
            title = file_content.split('\n')[0]
            if title.startswith('### '):
                title = title[4:]
            elif title == '':
                continue
            #include link to project page in title
            title = f'<a href="{links[file.split(".")[0]]}" target="_blank">{title}</a>'
            summary = file_content.split('\n', 1)[1].strip()
            summaries.append({
                'name': file.split('.')[0],
                'summary': summary,
                'title': title,
                "image": f"static/images/{file.split('.')[0]}.png"
            })
    return summaries

def get_plot_data(): 
    dfs = {}
    shortnames = get_shortnames()

    result_files = os.listdir('results')
        
    for file in result_files:
        #read csvs
        df = pd.read_csv(f'results/{file}')
        df['Submethod'] = df['Submethod'].astype('string').fillna('').replace('<NA>', '')
        df["Shortname"] = df["Method"].apply(lambda x: shortnames[x])
        df["NewMethod"] = df["Shortname"] + df["Submethod"]
        
        #change Size [Bytes] to Size [MB] and round
        if "Size [Bytes]" in df.columns:
            df["Size [MB]"] = df["Size [Bytes]"] / 1024 / 1024
            df["Size [MB]"] = df["Size [MB]"].apply(lambda x: round(x, 1))
            df.drop(columns=["Size [Bytes]"], inplace=True)

        dfs[file.split(".")[0]] = df

    shortnames = sorted(shortnames.values())

    data = []
    for dataset in dataset_order:
        df = dfs[dataset]

        psnr_size = []
        ssim_size = []
        lpips_size = []
        for method in df.index:
            psnr_size.append({"x": df.loc[method, "Size [MB]"], "y": df.loc[method, "PSNR"], "label": df.loc[method, "NewMethod"], "group": df.loc[method, "Shortname"], "group_id": shortnames.index(df.loc[method, "Shortname"])})
            ssim_size.append({"x": df.loc[method, "Size [MB]"], "y": df.loc[method, "SSIM"], "label": df.loc[method, "NewMethod"], "group": df.loc[method, "Shortname"], "group_id": shortnames.index(df.loc[method, "Shortname"])})
            lpips_size.append({"x": df.loc[method, "Size [MB]"], "y": df.loc[method, "LPIPS"], "label": df.loc[method, "NewMethod"], "group": df.loc[method, "Shortname"], "group_id": shortnames.index(df.loc[method, "Shortname"])})

        data.append({
            'plot1': {
                "title": f"<b>{dataset}</b>", #: PSNR / Size
                "xaxis": "Size (MB)",
                "yaxis": "PSNR",
                'points': psnr_size,
                'lines': []
            },
            'plot2': {
                "title": f"<b>{dataset}</b>", #: SSIM / Size
                "xaxis": "Size (MB)",
                "yaxis": "SSIM",
                'points': ssim_size,
                'lines': []
            },
            'plot3': {
                "title": f"<b>{dataset}</b>", #: LPIPS / Size
                "xaxis": "Size (MB)",
                "yaxis": "LPIPS",
                'points': lpips_size,
                'lines': []
            } 
        })

    group_links = {}
    shortnames = get_shortnames()
    for method in shortnames:
        group_links[shortnames[method]] = "#"+method

    return data, group_links

if __name__ == "__main__":
    results_table = combine_tables_to_html()
    summaries = load_methods_summaries()
    plot_data, group_links = get_plot_data()

    # Pfad zu deinem Template-Ordner
    file_loader = FileSystemLoader('project-page')
    env = Environment(loader=file_loader)

    # Lade das Template
    template = env.get_template('index_template.html')

    # Daten, die in das Template eingefügt werden sollen
    data = {
        'results_table': results_table,
        'summaries': summaries,
        'plot_data': json.dumps(plot_data),
        'group_links': json.dumps(group_links)
    }

    # Render das Template mit den Daten
    output = template.render(data)

    # Speichere das gerenderte HTML in einer Datei
    with open('project-page/index.html', 'w') as f:
        f.write(output)