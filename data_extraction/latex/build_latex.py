import os
import subprocess
from pathlib import Path
import bibtexparser
import pandas as pd
import io
from decimal import Decimal

methodsdir = "../../methods"
imagedir = "../../project-page/static/images/"
imagedir = "images/"
dataset_order = ["TanksAndTemples", "MipNeRF360", "DeepBlending", "SyntheticNeRF"]

# List of markdown files to combine
markdown_files = os.listdir(methodsdir)
image_files = os.listdir(imagedir)

# Combined markdown content
combined_markdown = ""
section_count = 1

with open("tex_templates/preamble.tex", "r") as file:
    tex_preamble = file.read()

with open("tex_templates/end_document.tex", "r") as file:
    tex_end_document = file.read()

with open("tex_templates/figure.tex", "r") as file:
    tex_figure = file.read()

with open("tex_templates/entry.tex", "r") as file:
    tex_entry = file.read()

with open("tex_templates/table.tex", "r") as file:
    tex_table = file.read()


def get_shortnames():
    # get shortnames from bibtex
    shortnames = {}
    with open("../../methods.bib") as bibtex_file:
        bib_database = bibtexparser.load(bibtex_file)
        for entry in bib_database.entries:
            if "shortname" in entry:
                shortnames[entry["ID"]] = entry["shortname"]
            else:
                shortnames[entry["ID"]] = entry["ID"]
                print(f"Shortname not found for {entry['ID']}, using ID instead")
    return shortnames


def generate_tex_table():
    dfs = []
    shortnames = get_shortnames()

    for dataset in dataset_order:
        # read csvs
        df = pd.read_csv(
            f"../../results/{dataset}.csv",
            dtype={"PSNR": str, "SSIM": str, "LPIPS": str},
        )
        # drop columns if [N/T] in Comment
        df = df[~df["Comment"].str.contains(r"\[N/T\]", na=False)]

        # parse all float columns to float and keep the exact numer of decimal places
        df["PSNR"] = df["PSNR"].apply(lambda x: Decimal(x) if x != "" else None)
        df["SSIM"] = df["SSIM"].apply(lambda x: Decimal(x) if x != "" else None)
        df["LPIPS"] = df["LPIPS"].apply(lambda x: Decimal(x) if x != "" else None)

        df["Submethod"] = (
            df["Submethod"].astype("string").fillna("").replace("<NA>", "")
        )

        # combine Method and Submethods colum into new Method column, replace method name with shortname+submethod
        df["NewMethod"] = df["Method"].apply(lambda x: shortnames[x])
        df["NewMethod"] = df["NewMethod"] + df["Submethod"]
        # make Method column a link to the method summary
        df["Method"] = df["NewMethod"]

        df.drop(columns=["Submethod", "NewMethod"], inplace=True)
        df.set_index("Method", inplace=True)
        # remove colums "Data Source" and "Comment"
        df.drop(columns=["Data Source", "Comment"], inplace=True)

        # change Size [Bytes] to Size [MB] and round
        if "Size [Bytes]" in df.columns:
            df["Size [MB]"] = df["Size [Bytes]"] / 1024 / 1024
            df["Size [MB]"] = df["Size [MB]"].apply(lambda x: round(x, 1))
            df.drop(columns=["Size [Bytes]"], inplace=True)

        dfs.append((dataset.split(".")[0], df))

    multi_col_df = pd.concat({name: df for name, df in dfs}, axis=1)
    multi_col_df.reset_index(inplace=True)

    # # fix unicode for lambda (only needed if all methods are included in table)
    # multi_col_df["Method"] = multi_col_df["Method"].str.replace("λ", "$\lambda$")

    # calculate ranking for each method: points for ranks in PSNR, SSIM and LPIPS and size,
    # add new ranking col right after the method name
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
                dataset_rank += (
                    multi_col_df[(dataset, metric)].rank(ascending=False) / 6
                )

        multi_col_df["Rank"] += dataset_rank.fillna(0)
        dataset_count += dataset_rank.notna()

    multi_col_df["Rank"] = (multi_col_df["Rank"] / dataset_count).apply(
        lambda x: round(x, 1)
    )

    # color the top 1 values in each column (top 3 on website)
    def add_top_3_classes(df):
        for col in df.columns:
            try:
                float_col = df[col].astype(float)
            except ValueError:
                continue

            if (
                any(keyword in col[1].lower() for keyword in ["size", "lpips"])
                or "rank" in col[0].lower()
            ):
                top_3 = pd.Series(float_col.unique()).nsmallest(1)
            else:
                top_3 = pd.Series(float_col.unique()).nlargest(1)
            for _, val in enumerate(top_3):
                matching_indices = float_col[float_col == val].index
                for index in matching_indices:
                    df.at[index, col] = f"\\textbf{{{df.at[index, col]}}}"
        return df

    # convert all columns to string to avoid FutureWarning, handle empty values/nans
    multi_col_df = add_top_3_classes(multi_col_df.astype(str)).replace(
        ["nan", "NaN"], ""
    )

    buffer = io.StringIO()
    multi_col_df.to_latex(buf=buffer, na_rep="", index=False, float_format="%.3g")

    lines = buffer.getvalue().strip().split("\n")
    lines[0] = "\\begin{tabular}{ll|llll|llll|llll|llll}"
    lines[3] = (
        lines[3]
        .replace("&", "& \\tiny")
        .replace("Size [MB]", "\\makecell{Size \\\\ MB}")
    )
    return "\n".join(lines)


def extract_title_and_text(markdown: str):
    markdown = markdown.strip()
    lines = markdown.split("\n")
    assert lines[0].startswith("#")
    # We assume that there are no hashtags in the title.
    # Who puts hashtags in a title anyway?
    title = lines[0].replace("#", "").strip()
    text = "\n".join(lines[1:]).strip()
    return title, text


def generate_section(paper_title: str, paper_text: str, paper_id: str, figure: str):
    global tex_entry
    section = tex_entry.replace("<paper_title>", paper_title)
    section = section.replace("<paper_text>", paper_text)
    section = section.replace("<paper_id>", paper_id)
    section = section.replace("<figure>", figure)
    return section


table = tex_table.replace("<table>", generate_tex_table())

tex_content = "\\section*{Contribution Summaries}\n\n The following sections provide brief summaries of the current contributions. For more detailed insights, please refer to the cited papers."
for filename in markdown_files:
    with open(os.path.join(methodsdir, filename), "r") as file:
        title, text = extract_title_and_text(file.read())
        paper_id = Path(filename).stem
        image_name = paper_id
        image_path = os.path.join(imagedir, image_name)

        figure_template = tex_figure.replace("<image_path>", image_path)
        latex_section = generate_section(title, text, paper_id, figure_template)
        tex_content += "\n\n" + latex_section

full_document = tex_preamble + table + tex_content + tex_end_document

with open("3dgs_compression_survey.tex", "w", encoding="UTF-8") as file:
    file.write(full_document)

# Step 4: Compile LaTeX Document
subprocess.run(["pdflatex", "3dgs_compression_survey.tex"])
# name of generated .bbl must match name of .tex file for arxiv submisisons
subprocess.run(["bibtex", "3dgs_compression_survey"])
subprocess.run(["pdflatex", "3dgs_compression_survey.tex"])
subprocess.run(["pdflatex", "3dgs_compression_survey.tex"])
subprocess.run(["open", "3dgs_compression_survey.pdf"])

# Delete all unnecessary files
subprocess.run(
    [
        "rm",
        "3dgs_compression_survey.aux",
        # "3dgs_compression_survey.bbl", # .bbl file needed for arxiv submission
        "3dgs_compression_survey.blg",
        "3dgs_compression_survey.log",
        "3dgs_compression_survey.out",
    ]
)
