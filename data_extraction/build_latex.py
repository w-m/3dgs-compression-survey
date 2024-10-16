import os
import subprocess
from pathlib import Path
import bibtexparser
import pandas as pd
import numpy as np
import io
from decimal import Decimal
import shutil
import re
import itertools

methodsdir = "../../methods"
imagedir = "../../project-page/static/images/"
imagedir = "images/"
dataset_order = ["TanksAndTemples", "MipNeRF360", "DeepBlending", "SyntheticNeRF"]

# List of markdown files to combine
markdown_files = os.listdir(methodsdir)

# Combined markdown content
combined_markdown = ""
section_count = 1

with open("tex_templates/figure.tex", "r") as file:
    tex_figure = file.read()

with open("tex_templates/entry.tex", "r") as file:
    tex_entry = file.read()

with open("tex_templates/table.tex", "r") as file:
    tex_table = file.read()

with open("tex_templates/contributions.tex", "r") as file:
    contributions = file.read()


def get_shortnames():
    # get shortnames from bibtex
    shortnames = {}
    with open("../../methods_compression.bib") as bibtex_file:
        bib_database = bibtexparser.load(bibtex_file)
        for entry in bib_database.entries:
            if "shortname" in entry:
                shortnames[entry["ID"]] = entry["shortname"]
            else:
                pass
                # shortnames[entry["ID"]] = entry["ID"]
                # print(f"Shortname not found for {entry['ID']}, using ID instead")
    return shortnames


def generate_tex_table():
    dfs = []
    shortnames = get_shortnames()

    groupcolors = {}
    colors = [
        "#1f77b4",
        "#aec7e8",
        "#ff7f0e",
        "#ffbb78",
        "#2ca02c",
        "#98df8a",
        "#d62728",
        "#ff9896",
        "#9467bd",
        "#c5b0d5",
        "#8c564b",
        "#c49c94",
        "#e377c2",
        "#f7b6d2",
        "#7f7f7f",
        "#c7c7c7",
        "#bcbd22",
        "#dbdb8d",
        "#17becf",
        "#9edae5",
    ]

    for name in shortnames.values():
        if name not in ["F-3DGS", "MesonGS"]:
            groupcolors[name] = colors.pop(0)

    for dataset in dataset_order:
        # read csvs
        df = pd.read_csv(
            f"../../results/{dataset}.csv",
            dtype={"PSNR": str, "SSIM": str, "LPIPS": str},
        )
        # drop columns if [N/T] in Comment
        df = df[~df["Comment"].str.contains(r"\[N/T\]", na=False)]
        # drop all rows with empty Submethod
        df = df[df["Submethod"].notna()]
        # filter out "Baseline" keyword from Submethod
        df["Submethod"] = df["Submethod"].str.replace("Baseline", "")

        # parse all float columns to float and keep the exact numer of decimal places
        df["PSNR"] = df["PSNR"].apply(lambda x: Decimal(x) if x != "" else None)
        df["SSIM"] = df["SSIM"].apply(lambda x: Decimal(x) if x != "" else None)
        df["LPIPS"] = df["LPIPS"].apply(lambda x: Decimal(x) if x != "" else None)

        # round psnr to max 2 decimal places
        df["PSNR"] = df["PSNR"].apply(lambda x: round(x, 2) if x is not None else None)

        df["Submethod"] = (
            df["Submethod"].astype("string").fillna("").replace("<NA>", "")
        )

        # combine Method and Submethods colum into new Method column, replace method name with shortname+submethod
        df["Shortname"] = df["Method"].apply(lambda x: shortnames[x])
        df["NewMethod"] = df["Shortname"] + df["Submethod"]
        # make Method column a link to the method summary
        df["Method"] = df["NewMethod"]

        # change Size [Bytes] to Size [MB] and round
        df["Size [MB]"] = df["Size [Bytes]"] / 1024 / 1024
        df["Size [MB]"] = df["Size [MB]"].apply(lambda x: round(x, 1))

        # divide by 1000 and add "k" to the number, empty string if nan
        df["k Gauss"] = df["#Gaussians"].apply(
            lambda x: f"{int(x/1000)}" if not pd.isna(x) else np.nan
        )
        # add , if more than 3 digits
        df["k Gauss"] = df["k Gauss"].apply(
            lambda x: "{:,}".format(int(x)) if not pd.isna(x) else np.nan
        )

        # calculate bits per gaussian
        df["b/G"] = (df["Size [Bytes]"] * 8 / df["#Gaussians"]).round()
        df["b/G"] = df["b/G"].apply(lambda x: str(int(x)) if not pd.isna(x) else np.nan)

        df.set_index("Method", inplace=True)
        # drop columns
        df.drop(
            columns=[
                "Submethod",
                "NewMethod",
                "Data Source",
                "Comment",
                "Shortname",
                "#Gaussians",
                "Size [Bytes]",
            ],
            inplace=True,
        )

        dfs.append((dataset, df))

    multi_col_df = pd.concat({name: df for name, df in dfs}, axis=1)
    multi_col_df.reset_index(inplace=True)

    # # fix unicode for lambda (only needed if all methods are included in table)
    # multi_col_df["Method"] = multi_col_df["Method"].str.replace("λ", "$\lambda$")

    # calculate ranking for each method: points for ranks in PSNR, SSIM and LPIPS and size,
    # add new ranking col right after the method name
    multi_col_df.insert(1, "Rank", 0)

    def get_metric_formula(mt_comb):
        formula_parts = []
        quality_metrics_weight = (
            (len(mt_comb) - 1) * 2 if "Size [MB]" in mt_comb else len(mt_comb)
        )

        if len(mt_comb) > 1:
            for metric in mt_comb:
                if metric == "Size [MB]":
                    formula_parts.append(
                        f"\\frac{{\\text{{rank}}( \\textbf{{{metric}}} )}}{{2}}"
                    )
                else:
                    formula_parts.append(
                        f"\\frac{{\\text{{rank}}( \\textbf{{{metric}}} )}}{{{quality_metrics_weight}}}"
                    )
        else:
            formula_parts.append(f"\\text{{rank}}(\\text{{{mt_comb[0]}}})")

        formula = "\\textbf{{Dataset rank}} = " + " + ".join(formula_parts)

        return formula

    def get_ranks(
        multi_col_df,
        metrics=["PSNR", "SSIM", "LPIPS", "Size [MB]"],
        datasets=dataset_order,
    ):
        dataset_count = multi_col_df["Rank"].copy()
        total_rank = multi_col_df["Rank"].copy()
        for dataset in datasets:
            dataset_rank = multi_col_df["Rank"].copy() * 0
            for metric in metrics:
                # calc weights for metrics
                if "Size [MB]" in metrics:
                    if len(metrics) == 1:
                        size_weight = 1
                        quality_metrics_weight = None
                    else:
                        size_weight = 2
                        quality_metrics_weight = (len(metrics) - 1) * 2
                else:
                    size_weight = None
                    quality_metrics_weight = len(metrics)

                if metric == "Size [MB]":
                    dataset_rank += (
                        multi_col_df[(dataset, metric)].rank(ascending=True)
                        / size_weight
                    )
                elif metric == "LPIPS":
                    dataset_rank += (
                        multi_col_df[(dataset, metric)].rank(ascending=True)
                        / quality_metrics_weight
                    )
                else:
                    dataset_rank += (
                        multi_col_df[(dataset, metric)].rank(ascending=False)
                        / quality_metrics_weight
                    )

            total_rank += dataset_rank.fillna(0)
            dataset_count += dataset_rank.notna()

        total_rank = (total_rank / dataset_count).apply(lambda x: round(x, 1))

        return total_rank

    # calc ranks for any combination of metrics and datasets
    datasets = dataset_order
    metrics = ["PSNR", "SSIM", "LPIPS", "Size [MB]"]
    rank_combinations = {}
    metric_formulas = {}
    for r_datasets in range(1, 5):  # Sizes 1 to 4 for dataset combinations
        for r_metrics in range(1, 5):  # Sizes 1 to 4 for metric combinations
            for ds_comb in itertools.combinations(datasets, r_datasets):
                for mt_comb in itertools.combinations(metrics, r_metrics):
                    result = get_ranks(multi_col_df, mt_comb, ds_comb)
                    # get bitwise combination vector for later identification
                    combination_vector = [
                        1 if metric in mt_comb else 0 for metric in metrics
                    ] + [1 if dataset in ds_comb else 0 for dataset in datasets]
                    combination_str = "".join(map(str, combination_vector))

                    # add top 3 classes to the result
                    classes = ["first", "second", "third"]
                    result_classes = result.copy().astype(str)
                    result_classes[:] = ""

                    top_3 = pd.Series(result.unique()).nsmallest(3)
                    for i, val in enumerate(top_3):
                        matching_indices = result[result == val].index
                        for index in matching_indices:
                            result_classes[index] = classes[i]

                    result = result.astype(str).replace("nan", "")
                    rank_combinations[combination_str] = (
                        result.to_list(),
                        result_classes.to_list(),
                    )

                    metric_formulas[combination_str[:4]] = get_metric_formula(mt_comb)

    multi_col_df["Rank"] = get_ranks(multi_col_df)

    ranks = {}
    i = 0
    # ranks for order of plot legend and summaries
    for index, row in multi_col_df.sort_values("Rank").iterrows():
        for shortname in shortnames.values():
            if shortname in row["Method"][0] and shortname not in ranks:
                ranks[shortname] = i
                i += 1
                break
    # sort group colors by rank for correct roder in legend
    groupcolors = {
        k: v for k, v in sorted(groupcolors.items(), key=lambda item: ranks[item[0]])
    }

    # sort by rank
    multi_col_df = multi_col_df.sort_values(by="Rank")

    # color the top 3 values in each column (top 3 in LaTeX)
    def add_top_3_classes(df):
        colors = ["lightred", "lightorange", "lightyellow"]
        for col in df.columns:
            try:
                float_col = df[col].str.replace(",", "").astype(float)
            except ValueError:
                continue

            if (
                any(
                    keyword in col[1].lower()
                    for keyword in ["size", "lpips", "gauss", "b/g"]
                )
                or "rank" in col[0].lower()
            ):
                top_3 = pd.Series(float_col.unique()).nsmallest(3)
            else:
                top_3 = pd.Series(float_col.unique()).nlargest(3)
            for i, val in enumerate(top_3):
                matching_indices = float_col[float_col == val].index
                for index in matching_indices:
                    df.at[index, col] = f"\\cellcolor{{{colors[i]}}}{df.at[index, col]}"
        return df

    # convert all columns to string to avoid FutureWarning, handle empty values/nans
    multi_col_df = add_top_3_classes(multi_col_df.astype(str)).replace(
        ["nan", "NaN"], ""
    )

    buffer = io.StringIO()
    multi_col_df.to_latex(buf=buffer, na_rep="", index=False, float_format="%.3g")

    lines = buffer.getvalue().strip().split("\n")
    lines[0] = "\\begin{tabular}{ll|llllll|llllll|llllll|llllll}"
    lines[2] = (
        lines[2]
        .replace("{r}", "{c|}")
        .replace("{c|}{SyntheticNeRF}", "{c}{SyntheticNeRF}")
    )
    lines[3] = (
        lines[3]
        .replace("&", "& \\tiny")
        .replace("PSNR", "PSNR$\\uparrow$")
        .replace("SSIM", "SSIM$\\uparrow$")
        .replace("LPIPS", "LPIPS$\\downarrow$")
        .replace("Size [MB]", "\\makecell{Size \\\\ MB$\\downarrow$}")
        .replace("#Gauss", "$\\#$Gauss")
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
    # check for html
    clean = re.compile("<.*?>")
    text = re.sub(clean, "", text)
    # excape % character
    text = text.replace("%", r"\%")
    return title, text


def generate_section(paper_title: str, paper_text: str, paper_id: str, figure: str):
    global tex_entry
    section = tex_entry.replace("<paper_title>", paper_title)
    section = section.replace("<paper_text>", paper_text)
    section = section.replace("<paper_id>", paper_id)
    section = section.replace("<figure>", figure)
    return section


def cp_images(src_folder, dst_folder):
    # Ensure the destination folder exists
    if not os.path.exists(dst_folder):
        os.makedirs(dst_folder)

    # Get the list of images in both folders
    images_in_src = [
        f
        for f in os.listdir(src_folder)
        if os.path.isfile(os.path.join(src_folder, f))
        and f.lower().endswith((".png", ".jpg", ".jpeg", ".gif", ".bmp", ".tiff"))
    ]
    images_in_dst = set(os.listdir(dst_folder))

    # Copy images from source to destination if they are not already in folder B
    for image in images_in_src:
        if image not in images_in_dst:
            src = os.path.join(src_folder, image)
            dst = os.path.join(dst_folder, image)
            shutil.copy2(src, dst)
            print(f"Copied: {image}")

    print("Copying complete!")


# copy images from website folder into latex folder
src_folder = "../../project-page/static/images"
cp_images(src_folder, "images")

# copy bib files into latex folder
shutil.copy2("../../datasets.bib", "dataset.bib")
shutil.copy2("../../methods.bib", "methods.bib")

# create table
table = tex_table.replace("<table>", generate_tex_table())
with open("3dgs_table.tex", "w", encoding="UTF-8") as file:
    file.write(table)

# create subsections for methods
for filename in markdown_files:
    with open(os.path.join(methodsdir, filename), "r") as file:
        title, text = extract_title_and_text(file.read())
        paper_id = Path(filename).stem
        image_name = paper_id
        image_path = os.path.join(imagedir, image_name)

        figure_template = tex_figure.replace("<image_path>", image_path)
        latex_section = generate_section(title, text, paper_id, figure_template)
        contributions += "\n\n" + latex_section

# create contributions
with open("3dgs_contributions.tex", "w", encoding="UTF-8") as file:
    file.write(contributions)

# Compile LaTeX Document
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
        "3dgs_compression_survey.blg",
        "3dgs_compression_survey.log",
        "3dgs_compression_survey.out",
        "dataset.bib",
        "methods.bib",
    ]
)

# Run arXiv script
subprocess.run(["arxiv_latex_cleaner", "../latex"])
subprocess.run(["rm", "../latex_arXiv/build_latex.py", "../latex_arXiv/3dgs_table.tex"])
shutil.make_archive(
    "../latex_arXiv", format="zip", root_dir="../", base_dir="latex_arXiv"
)
