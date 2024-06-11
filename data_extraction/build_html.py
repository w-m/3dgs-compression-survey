import os
import pandas as pd
import bibtexparser

def get_shortnames():
    #get shortnames from bibtex
    shortnames = {}
    with open("methods.bib") as bibtex_file:
        bib_database = bibtexparser.load(bibtex_file)
        for entry in bib_database.entries:
            if "shortname" in entry:
                shortnames[entry["ID"]] = entry["shortname"]
            else:
                shortnames[entry["ID"]] = entry["ID"]
                print(f"Shortname not found for {entry['ID']}, using ID instead")
    return shortnames


def combine_tables_to_html():
    dfs = []
    for file in os.listdir('results'):
        #read csvs
        df = pd.read_csv(f'results/{file}')
        df.set_index("Method", inplace=True)
        #remove colum "Data Source"
        df.drop(columns=["Data Source"], inplace=True)
        df.drop(columns=["Comment"], inplace=True)

        #change Size [Bytes] to Size [MB] and round
        if "Size [Bytes]" in df.columns:
            df["Size [MB]"] = df["Size [Bytes]"] / 1024 / 1024
            df["Size [MB]"] = df["Size [MB]"].apply(lambda x: round(x, 1))
            df.drop(columns=["Size [Bytes]"], inplace=True)

        dfs.append((file.split(".")[0], df))
    
    multi_col_df = pd.concat({name: df for name, df in dfs}, axis=1)
    multi_col_df.reset_index(inplace=True)
    html_string = multi_col_df.to_html(na_rep='', index=False, table_id="results", classes=["display", "cell-border"], justify="center", border=0)
    
    # with open("project-page/results.html", "w") as f:
    #     f.write(html_string)
    return html_string


if __name__ == "__main__":
    table = combine_tables_to_html()