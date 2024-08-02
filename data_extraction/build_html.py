import os
import pandas as pd
import bibtexparser
from jinja2 import Environment, FileSystemLoader
import re
import json
from decimal import Decimal
from PIL import Image

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

def get_authors():
    #get authors from bibtex
    authors = {}
    with open("methods.bib", encoding='utf-8') as bibtex_file:
        bib_database = bibtexparser.load(bibtex_file)
        for entry in bib_database.entries:
            if "author" in entry:
                authors[entry["ID"]] = entry["author"]
            else:
                authors[entry["ID"]] = ""
                print(f"Author not found for {entry['ID']}")
    return authors


def combine_tables_to_html():
    dfs = []
    shortnames = get_shortnames()

    groupcolors = {}
    # group_colors = plotly.colors.qualitative.Prism
    colors = [
    "#1f77b4", "#aec7e8", "#ff7f0e", "#ffbb78",
    "#2ca02c", "#98df8a", "#d62728", "#ff9896",
    "#9467bd", "#c5b0d5", "#8c564b", "#c49c94",
    "#e377c2", "#f7b6d2", "#7f7f7f", "#c7c7c7",
    "#bcbd22", "#dbdb8d", "#17becf", "#9edae5"
    ]
    for name in shortnames.values():
        if name not in ["F-3DGS"]:
            groupcolors[name] = colors.pop(0)

    for dataset in dataset_order:
        #read csvs
        df = pd.read_csv(f'results/{dataset}.csv', dtype={'PSNR': str, 'SSIM': str, 'LPIPS': str})
        #drop rows if [N/T] in Comment
        df = df[~df['Comment'].str.contains(r'\[N/T\]', na=False)]
        #drop all rows with empty Submethod
        df = df[df['Submethod'].notna()]
        #filter out "Baseline" keyword from Submethod
        df['Submethod'] = df['Submethod'].str.replace('Baseline', '')

        # parse all float columns to float and keep the exact numer of decimal places
        df["PSNR"] = df["PSNR"].apply(lambda x: Decimal(x) if x != '' else None)
        df["SSIM"] = df["SSIM"].apply(lambda x: Decimal(x) if x != '' else None)
        df["LPIPS"] = df["LPIPS"].apply(lambda x: Decimal(x) if x != '' else None)


        df['Submethod'] = df['Submethod'].astype('string').fillna('').replace('<NA>', '')

        #combine Method and Submethods colum into new Method column, replace method name with shortname+submethod
        df["Shortname"] = df["Method"].apply(lambda x: shortnames[x])
        df["NewMethod"] = df["Shortname"] + df["Submethod"]
        # make Method column a link to the method summary + add color box
        df["Method"] = '<a class="method-name" href="#' + df["Method"] + '"> <span class="legend-color-box-container"><span class="legend-color-box" style=background-color:'+df["Shortname"].map(groupcolors)+'></span><span class="legend-color-box-methods"></span>' + df["NewMethod"] + '</span></a>'

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
    #add new ranking col right after the method name
    multi_col_df.insert(1, "Rank", 0)

    dataset_count = multi_col_df["Rank"].copy()
    for dataset in dataset_order:
        dataset_rank = multi_col_df["Rank"].copy() * 0
        for metric in ["PSNR", "SSIM", "LPIPS", "Size [MB]"]:
            if metric == "Size [MB]":
                dataset_rank += multi_col_df[(dataset, metric)].rank(ascending=True) / 2
            elif metric == "LPIPS":
                dataset_rank += multi_col_df[(dataset, metric)].rank(ascending=True) / 6
            else:
                dataset_rank += multi_col_df[(dataset, metric)].rank(ascending=False) / 6
        
        multi_col_df["Rank"] += dataset_rank.fillna(0)
        dataset_count += dataset_rank.notna()
    
    multi_col_df["Rank"] = (multi_col_df["Rank"] / dataset_count).apply(lambda x: round(x, 1))

    ranks = {}
    i = 0
    #ranks for order of plot legend and summaries
    for index, row in multi_col_df.sort_values("Rank").iterrows():
        for shortname in shortnames.values():
            if shortname in row["Method"][0] and shortname not in ranks:
                ranks[shortname] = i
                i += 1
                break
    #sort group colors by rank for correct roder in legend
    groupcolors = {k: v for k, v in sorted(groupcolors.items(), key=lambda item: ranks[item[0]])}

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
    
    #convert all columns to string to avoid FutureWarning, handle empty values/nans
    multi_col_df = add_top_3_classes(multi_col_df.astype(str)).replace(['nan', 'NaN'], '')

    html_string = multi_col_df.to_html(na_rep='', index=False, table_id="results", classes=["display", "cell-border"], 
                                      justify="center", border=0, escape=False)

    # Function to clean up nested <td> elements using regex
    def clean_nested_td(html):
        pattern = re.compile(r'<td><td([^>]*)>([^<]*)<\/td><\/td>')
        cleaned_html = pattern.sub(r'<td\1>\2</td>', html)
        return cleaned_html

    # Clean the HTML string
    cleaned_html_string = clean_nested_td(html_string)

    return cleaned_html_string, ranks, groupcolors

def get_published_at():
    published_at = {}
    with open("methods.bib", encoding='utf-8') as bibtex_file:
        bib_database = bibtexparser.load(bibtex_file)
        for entry in bib_database.entries:
            if "booktitle" in entry:
                pub = entry["booktitle"]
            elif "journal" in entry:
                pub = entry["journal"] 
            else:
                pub = "arXiv"
            
            if pub != "arXiv":
                if "Conference on Computer Vision and Pattern Recognition" in pub:
                    pub = "CVPR"
                elif "European Conference on Computer Vision" in pub:
                    pub = "ECCV"
                elif "ACM on Computer Graphics and Interactive Techniques" in pub:
                    pub = "I3D"
                elif "ACM Transactions on Graphics" in pub:
                    pub = "TOG"
                
                pub = pub + " '" + entry["year"][-2:]

            published_at[entry["ID"]] = pub
            
    return published_at

def load_methods_summaries(ranks, groupcolors):
    # Load the summaries of the methods
    summaries = []
    links = get_links()
    authors = get_authors()
    published_at = get_published_at()

    #sort here by rank to determine order of method summaries
    shortnames = get_shortnames()
    for name in shortnames.values(): #also include non ranked methods
        if name not in ranks:
            ranks[name] = 1000

    for shortname in ranks.keys():
        file = [key for key, value in shortnames.items() if value == shortname][0] + '.md'
        with open(f'methods/{file}', 'r') as f:
            file_content = f.read()
            # markdown files, extarct title and summary
            title = file_content.split('\n')[0]
            if title.startswith('### '):
                title = title[4:]
            elif title == '':
                continue
            #include link to project page in title, if available
            if links[file.split(".")[0]] != '':
                try:
                    color = groupcolors[shortnames[file.split(".")[0]]]
                except KeyError:
                    color = "#ffffff"
                title = f'<a href="{links[file.split(".")[0]]}" target="_blank" class="title-link" style="--title-box-color: {color}">{title}</a>'
            summary = file_content.split('\n', 1)[1].strip()

            #get image path, webp, png or jpg
            if os.path.exists(f"project-page/static/images/{file.split('.')[0]}_small.webp"):
                image = f"static/images/{file.split('.')[0]}_small.webp"
            elif os.path.exists(f"project-page/static/images/{file.split('.')[0]}.webp"):
                image = f"static/images/{file.split('.')[0]}.webp"
            elif os.path.exists(f"project-page/static/images/{file.split('.')[0]}.png"):
                image = f"static/images/{file.split('.')[0]}.png"
            elif os.path.exists(f"project-page/static/images/{file.split('.')[0]}.jpg"):
                image = f"static/images/{file.split('.')[0]}.jpg"
            else:
                image = ""

            #get width and height of image
            if image != "":
                with Image.open(f"project-page/{image}") as img:
                    width, height = img.size

            author = authors[file.split(".")[0]] 
            #replace all but the last " and " with ", "
            if not "," in author:
                parts = author.split(' and ')
                # Join all parts except the last one with ", " and then add the last part prefixed with " and "
                author = ', '.join(parts[:-1]) + ' and ' + parts[-1]

            summaries.append({
                'name': file.split('.')[0],
                'summary': summary,
                'title': title,
                'authors': author,
                'image': image,
                'imwidth': width,
                'imheight': height,
                'published_at': published_at[file.split(".")[0]]
            })
    return summaries

def get_plot_data(ranks): 
    dfs = {}
    shortnames = get_shortnames()

    result_files = os.listdir('results')
        
    for file in result_files:
        #read csvs
        df = pd.read_csv(f'results/{file}')
        df['Submethod'] = df['Submethod'].astype('string').fillna('').replace('<NA>', '')
        df["Shortname"] = df["Method"].apply(lambda x: shortnames[x])

        #filter out "Baseline" keyword from Submethod
        df['Submethod'] = df['Submethod'].str.replace('Baseline', ' baseline')

        df["NewMethod"] = df["Shortname"] + df["Submethod"]

        #remove from df if [N/P] in comment
        df = df[~df['Comment'].str.contains(r'\[N/P\]', na=False)]
        
        #change Size [Bytes] to Size [MB] and round
        if "Size [Bytes]" in df.columns:
            df["Size [MB]"] = df["Size [Bytes]"] / 1024 / 1024
            df["Size [MB]"] = df["Size [MB]"].apply(lambda x: round(x, 1))
            df.drop(columns=["Size [Bytes]"], inplace=True)

        dfs[file.split(".")[0]] = df

    shortnames = sorted(shortnames.values())

    org_3dgs = {
        "TanksAndTemples": [23.14, 0.841, 0.183] ,
        "MipNeRF360": [27.21, 0.815, 0.214],
        "DeepBlending": [29.41, 0.903, 0.243],
        "SyntheticNeRF": [33.32, None, None],
    }

    data = []
    for dataset in dataset_order:
        df = dfs[dataset]

        psnr_groupData = {}
        ssim_groupData = {}
        lpips_groupData = {}

        for method in df.index:
            if psnr_groupData.get(df.loc[method, "Shortname"]) is None:
                psnr_groupData[df.loc[method, "Shortname"]] = {"x": [], "y": [], "text": []}
            if ssim_groupData.get(df.loc[method, "Shortname"]) is None:
                ssim_groupData[df.loc[method, "Shortname"]] = {"x": [], "y": [], "text": []}
            if lpips_groupData.get(df.loc[method, "Shortname"]) is None:
                lpips_groupData[df.loc[method, "Shortname"]] = {"x": [], "y": [], "text": []}
            
            psnr_groupData[df.loc[method, "Shortname"]]["x"].append(df.loc[method, "Size [MB]"])
            psnr_groupData[df.loc[method, "Shortname"]]["y"].append(df.loc[method, "PSNR"])
            psnr_groupData[df.loc[method, "Shortname"]]["text"].append(df.loc[method, "NewMethod"])

            ssim_groupData[df.loc[method, "Shortname"]]["x"].append(df.loc[method, "Size [MB]"])
            ssim_groupData[df.loc[method, "Shortname"]]["y"].append(df.loc[method, "SSIM"])
            ssim_groupData[df.loc[method, "Shortname"]]["text"].append(df.loc[method, "NewMethod"])

            lpips_groupData[df.loc[method, "Shortname"]]["x"].append(df.loc[method, "Size [MB]"])
            lpips_groupData[df.loc[method, "Shortname"]]["y"].append(df.loc[method, "LPIPS"])
            lpips_groupData[df.loc[method, "Shortname"]]["text"].append(df.loc[method, "NewMethod"])   


        data.append({
            'plot1': {
                "title": f"<b>{dataset}</b>", #: PSNR / Size
                "xaxis": "Size (MB)",
                "yaxis": "PSNR",
                'groupData': psnr_groupData,
                'lines': [],
                'lineHeight': org_3dgs[dataset][0],
            },
            'plot2': {
                "title": f"<b>{dataset}</b>", #: SSIM / Size
                "xaxis": "Size (MB)",
                "yaxis": "SSIM",
                'groupData': ssim_groupData,
                'lines': [],
                'lineHeight': org_3dgs[dataset][1],
            },
            'plot3': {
                "title": f"<b>{dataset}</b>", #: LPIPS / Size
                "xaxis": "Size (MB)",
                "yaxis": "LPIPS",
                'groupData': lpips_groupData,
                'lines': [],
                'lineHeight': org_3dgs[dataset][2],
            } 
        })

    group_links = {}
    shortnames = get_shortnames()
    for method in shortnames:
        group_links[shortnames[method]] = "#"+method

    checkbox_states = {}
    for method in shortnames.values():
        if method in ["Scaffold-GS"]:
            checkbox_states[method] = False
        else:
            checkbox_states[method] = True


    return data, group_links, checkbox_states

if __name__ == "__main__":
    results_table, ranks, groupcolors = combine_tables_to_html()
    summaries = load_methods_summaries(ranks, groupcolors)
    plot_data, group_links, checkbox_states = get_plot_data(ranks)

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
        'group_links': json.dumps(group_links),
        'checkbox_states': json.dumps(checkbox_states),
        'groupcolors': json.dumps(groupcolors)
    }

    # Render das Template mit den Daten
    output = template.render(data)

    # Speichere das gerenderte HTML in einer Datei
    with open('project-page/index.html', 'w', encoding='utf-8') as f:
        f.write(output)