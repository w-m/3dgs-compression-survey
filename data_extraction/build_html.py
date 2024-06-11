import os
import pandas as pd
import bibtexparser
from jinja2 import Environment, FileSystemLoader
import re

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
    for file in os.listdir('results'):
        #read csvs
        df = pd.read_csv(f'results/{file}')
        df['Submethod'] = df['Submethod'].astype('string').fillna('').replace('<NA>', '')

        #combine Method and Submethods colum into new Method column, replace method name with shortname+submethod
        df["NewMethod"] = df["Method"].apply(lambda x: shortnames[x])
        df["NewMethod"] = df["NewMethod"] + df["Submethod"]
        # make Method column a link to the method summary
        df["Method"] = '<a href="#' + df["Method"] + '">' + df["NewMethod"] + '</a>'
        df.drop(columns=["Submethod", "NewMethod"], inplace=True)
        df.set_index("Method", inplace=True)
        #remove colums "Data Source" and "Comment"
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

    #color the top 3 values in each column
    def add_top_3_classes(df):
        colors = ['rgba(255, 215, 0, 0.5)', 'rgba(192, 192, 192, 0.5)', 'rgba(205, 127, 50, 0.5)']  # Gold, Silver, Bronze with reduced opacity
        for col in df.select_dtypes(include=[float, int]).columns:
            if 'size' in col[1].lower():
                top_3 = df[col].nsmallest(3)
            else:
                top_3 = df[col].nlargest(3)
            for i, val in enumerate(top_3):
                df.loc[df[col] == val, col] = f'<td style="background-color: {colors[i]}">{val}</td>'
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
            #<a href="https://github.com/eliahuhorwitz/Academic-project-page-template" target="_blank">title</a>
            title = f'<a href="{links[file.split(".")[0]]}" target="_blank">{title}</a>'
            summary = file_content.split('\n', 1)[1].strip()
            summaries.append({
                'name': file.split('.')[0],
                'summary': summary,
                'title': title,
                "image": f"static/images/{file.split('.')[0]}.png"
            })
    return summaries

if __name__ == "__main__":
    results_table = combine_tables_to_html()
    summaries = load_methods_summaries()

    # Pfad zu deinem Template-Ordner
    file_loader = FileSystemLoader('project-page')
    env = Environment(loader=file_loader)

    # Lade das Template
    template = env.get_template('index_template.html')

    # Daten, die in das Template eingefügt werden sollen
    data = {
        'results_table': results_table,
        'summaries': summaries
    }

    # Render das Template mit den Daten
    output = template.render(data)

    # Speichere das gerenderte HTML in einer Datei
    with open('project-page/index.html', 'w') as f:
        f.write(output)