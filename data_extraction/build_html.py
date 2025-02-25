import os
import pandas as pd
import bibtexparser
from jinja2 import Environment, FileSystemLoader
import re
import json
from decimal import Decimal
from PIL import Image
import numpy as np
import itertools

dataset_order = ["TanksAndTemples", "MipNeRF360", "DeepBlending", "SyntheticNeRF"]
dataset_names = {
    "TanksAndTemples": "Tanks and Temples",
    "MipNeRF360": "Mip-NeRF 360",
    "DeepBlending": "Deep Blending",
    "SyntheticNeRF": "Synthetic NeRF",
}

org_3dgs = {  # 30K
    "TanksAndTemples": ["23.14", "0.841", "0.183", 411000000, 1783867.00],
    "MipNeRF360": ["27.21", "0.815", "0.214", 734000000, 3362470.00],
    "DeepBlending": ["29.41", "0.903", "0.243", 676000000, 2975634.50],
    "SyntheticNeRF": ["33.31", None, None, None, None],
}

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
    "#ff00ff",
]
colors_d = [
    "#164f79",
    "#7a8da3",
    "#b2590a",
    "#b28253",
    "#1d721f",
    "#6ca46e",
    "#941d1d",
    "#b26b68",
    "#6b4d8a",
    "#897aa3",
    "#633e38",
    "#896e66",
    "#a05891",
    "#ae8093",
    "#595959",
    "#8d8d8d",
    "#868417",
    "#989867",
    "#1193b1",
    "#6ca0a2",
]


def get_shortnames(methods_files=["methods_compression.bib"]):
    # get shortnames from bibtex
    shortnames = {}
    for methods_file in methods_files:
        with open(methods_file) as bibtex_file:
            bib_database = bibtexparser.load(bibtex_file)
            for entry in bib_database.entries:
                if "shortname" in entry:
                    shortnames[entry["ID"]] = entry["shortname"]
                else:
                    pass
                    # shortnames[entry["ID"]] = entry["ID"]
                    # print(f"Shortname not found for {entry['ID']}, using ID instead")
    if "methods_compression.bib" in methods_files:
        shortnames["3DGS"] = "3DGS-30K"
    return shortnames


def get_links(methods_files=["methods_compression.bib", "methods_densification.bib"]):
    # get links from bibtex
    links = {}
    for methods_file in methods_files:
        with open(methods_file) as bibtex_file:
            bib_database = bibtexparser.load(bibtex_file)
            for entry in bib_database.entries:
                if "url" in entry:
                    links[entry["ID"]] = entry["url"]
                else:
                    links[entry["ID"]] = ""
                    print(f"Link not found for {entry['ID']}")
    return links


def get_authors(methods_files=["methods_compression.bib", "methods_densification.bib"]):
    # get authors from bibtex
    authors = {}
    for methods_file in methods_files:
        with open(methods_file, encoding="utf-8") as bibtex_file:
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
    shortnames_d = get_shortnames(methods_files=["methods_densification.bib"])

    groupcolors = {}

    method_categories_dict = {}
    for name, shortname in shortnames.items():
        if shortname not in ["F-3DGS"]:
            groupcolors[shortname] = colors.pop(0)
        method_categories_dict[name] = "c"

    for name, shortname in shortnames_d.items():
        if shortname not in ["F-3DGS"]:
            groupcolors[shortname] = colors_d.pop(0)
        method_categories_dict[name] = "d"

    method_categories_dict["3DGS"] = "3"

    shortnames.update(shortnames_d)

    for dataset in dataset_order:
        # read csvs
        df = pd.read_csv(
            f"results/{dataset}.csv",
            dtype={"PSNR": str, "SSIM": str, "LPIPS": str, "Comment": str},
        )
        # drop rows if [N/T] in Comment
        df = df[~df["Comment"].str.contains(r"\[N/T\]", na=False)]
        # drop all rows with empty Submethod
        df = df[df["Submethod"].notna()]
        # filter out "Baseline" keyword from Submethod
        df["Submethod"] = df["Submethod"].str.replace("Baseline", "")

        # # insert 3DGS
        # df = pd.concat(
        #     [
        #         df,
        #         pd.DataFrame(
        #             [
        #                 {
        #                     "Method": "3DGS",
        #                     "Submethod": "",
        #                     "PSNR": org_3dgs[dataset][0],
        #                     "SSIM": (
        #                         org_3dgs[dataset][1] if org_3dgs[dataset][1] else ""
        #                     ),
        #                     "LPIPS": (
        #                         org_3dgs[dataset][2] if org_3dgs[dataset][1] else ""
        #                     ),
        #                     "Size [Bytes]": org_3dgs[dataset][3],
        #                     "#Gaussians": org_3dgs[dataset][4],
        #                     "Data Source": "",
        #                     "Comment": "",
        #                 }
        #             ]
        #         ),
        #     ],
        #     ignore_index=True,
        # )

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
        # make Method column a link to the method summary + add color box
        df["Method"] = (
            '<a class="method-name" href="#'
            + df["Method"]
            + '"> <span class="legend-color-box-container">'
            + '<span class="'
            + df["Method"].apply(
                lambda x: (
                    "legend-color-box densification"
                    if x in shortnames_d
                    else "legend-color-box"
                )
            )
            + '" style="background-color:'
            + df["Shortname"].map(groupcolors)
            + '"></span>'
            + '<span class="legend-color-box-methods"></span>'
            + df["NewMethod"]
            + "</span></a>"
        )

        # change Size [Bytes] to Size [MB] and round
        df.insert(
            5, "Size [MB]", df["Size [Bytes]"] / 1000 / 1000
        )  # df.insert(5, "Size [MB]", df["Size [Bytes]"] / 1024 / 1024)
        df["Size [MB]"] = df["Size [MB]"].apply(lambda x: round(x, 1))

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
                "Size [Bytes]",
            ],
            inplace=True,
        )

        dfs.append((dataset, df))

    multi_col_df = pd.concat({name: df for name, df in dfs}, axis=1)
    multi_col_df.reset_index(inplace=True)

    # insert category
    multi_col_df[("category", "")] = "3"
    # Loop through method_categories_dict to set the category if the method name contains the key
    for method, category in method_categories_dict.items():
        multi_col_df.loc[
            multi_col_df["Method"].str.contains(f'"#{method}"', na=False), "category"
        ] = category

    method_categories = list(multi_col_df["category"])

    # calculate ranking for each method: points for ranks in PSNR, SSIM and LPIPS and size,
    # add new ranking col right after the method name
    multi_col_df.insert(1, "Rank", 0)

    def get_metric_formula(mt_comb):
        formula_parts = []
        quality_metrics_weight = (
            (len(mt_comb) - 1) * 2
            if "Size [MB]" in mt_comb or "#Gaussians" in mt_comb
            else len(mt_comb)
        )

        if len(mt_comb) > 1:
            for metric in mt_comb:
                if metric == "Size [MB]" or metric == "#Gaussians":
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

        formula = formula.replace("#", r"\#")  # prevent katex EOL error

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
                if "Size [MB]" in metrics or "#Gaussians" in metrics:
                    if len(metrics) == 1:
                        size_weight = 1
                        quality_metrics_weight = None
                    else:
                        size_weight = 2
                        quality_metrics_weight = (len(metrics) - 1) * 2
                else:
                    size_weight = None
                    quality_metrics_weight = len(metrics)

                rmethod = "min"
                if metric == "Size [MB]" or metric == "#Gaussians":
                    dataset_rank += (
                        multi_col_df[(dataset, metric)].rank(
                            ascending=True, method=rmethod
                        )
                        / size_weight
                    )
                elif metric == "LPIPS":
                    dataset_rank += (
                        multi_col_df[(dataset, metric)].rank(
                            ascending=True, method=rmethod
                        )
                        / quality_metrics_weight
                    )
                else:
                    dataset_rank += (
                        multi_col_df[(dataset, metric)].rank(
                            ascending=False, method=rmethod
                        )
                        / quality_metrics_weight
                    )

            total_rank += dataset_rank.fillna(0)
            dataset_count += dataset_rank.notna()

        total_rank = (total_rank / dataset_count).apply(lambda x: round(x, 1))
        return total_rank

    def get_rank_combinations_and_formulas(datasets, metrics, df):
        rank_combinations = {}
        metric_formulas = {}
        for r_datasets in range(1, len(datasets) + 1):
            for r_metrics in range(1, len(metrics) + 1):
                for ds_comb in itertools.combinations(datasets, r_datasets):
                    for mt_comb in itertools.combinations(metrics, r_metrics):
                        result = get_ranks(df, mt_comb, ds_comb)
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

                        metric_formulas[combination_str[:4]] = get_metric_formula(
                            mt_comb
                        )
        return rank_combinations, metric_formulas

    def filter_empty_cols_from_df(key):
        # set datasets where important metric is nan completly to nan to avoid influencing ranks of other methods when own rank cant be determined
        new_df = multi_col_df.copy()  # Make a copy of the original dataframe
        for dataset in dataset_order:
            new_df.loc[
                new_df[(dataset, key)].isna(),
                [(dataset, "PSNR"), (dataset, "SSIM"), (dataset, "LPIPS")],
            ] = np.nan
        return new_df

    # calc compression ranks for any combination of metrics and datasets for all methods
    datasets = dataset_order
    metrics = ["PSNR", "SSIM", "LPIPS", "Size [MB]"]
    rank_combinations_c_all, metric_formulas_c = get_rank_combinations_and_formulas(
        datasets, metrics, filter_empty_cols_from_df("Size [MB]")
    )

    # calc compression ranks for any combination of metrics and datasets for all compression methods +3DGS
    filter_c3 = (multi_col_df["category"] == "c") | (multi_col_df["category"] == "3")
    filtered_df = multi_col_df[filter_c3].copy()
    rank_combinations_c, _ = get_rank_combinations_and_formulas(
        datasets, metrics, filtered_df
    )

    # calc densification ranks for combinations of metrics and datasets for all methods
    datasets = dataset_order[:3]
    metrics = ["PSNR", "SSIM", "LPIPS", "#Gaussians"]
    rank_combinations_d_all, metric_formulas_d = get_rank_combinations_and_formulas(
        datasets, metrics, filter_empty_cols_from_df("#Gaussians")
    )

    # calc compression ranks for any combination of metrics and datasets for all densification methods +3DGS
    filter_d3 = (multi_col_df["category"] == "d") | (multi_col_df["category"] == "3")
    filtered_df = multi_col_df[filter_d3].copy()
    rank_combinations_d, _ = get_rank_combinations_and_formulas(
        datasets, metrics, filtered_df
    )

    rank_combinations = {
        "compression": rank_combinations_c,
        "densification": rank_combinations_d,
        "compression_all": rank_combinations_c_all,
        "densification_all": rank_combinations_d_all,
    }

    metric_formulas = {
        "compression": metric_formulas_c,
        "densification": metric_formulas_d,
    }

    def get_ordered_ranks():
        ranks = {}
        i = 0
        # ranks for order of plot legend and summaries
        for index, row in multi_col_df.sort_values("Rank").iterrows():
            for shortname in shortnames.values():
                if (
                    shortname in row["Method"].item()
                    and shortname not in ranks
                    and not np.isnan(row["Rank"].item())
                ):
                    ranks[shortname] = i
                    i += 1
                    break
        return ranks

    latex_dfs = {}
    ranks = {}
    # first get ordered densification ranks for summary order and plot legend order
    mask = (multi_col_df["category"] == "d") | (multi_col_df["category"] == "3")
    multi_col_df["Rank"] = pd.Series(
        rank_combinations["densification"]["1111111"][0][: mask.sum()],
        index=multi_col_df[mask].index,
    ).astype(float)
    ranks["d"] = get_ordered_ranks()
    latex_dfs["densification"] = multi_col_df.copy()

    # then same for compression and leave ranks like this as this is the default option on the website
    mask = (multi_col_df["category"] == "c") | (multi_col_df["category"] == "3")
    multi_col_df["Rank"] = pd.Series(
        rank_combinations["compression"]["11111111"][0][: mask.sum()],
        index=multi_col_df[mask].index,
    ).astype(float)
    ranks["c"] = get_ordered_ranks()
    latex_dfs["compression"] = multi_col_df.copy()

    # sort group colors by rank for correct order in legend
    groupcolors_d = {
        k: v
        for k, v in sorted(
            groupcolors.items(), key=lambda item: ranks["d"].get(item[0], float("inf"))
        )
        if k in ranks["d"]
    }
    groupcolors_c = {
        k: v
        for k, v in sorted(
            groupcolors.items(), key=lambda item: ranks["c"].get(item[0], float("inf"))
        )
        if k in ranks["c"]
    }
    groupcolors = {**groupcolors_c, **groupcolors_d}

    # color the top 3 values in each column
    def add_top_3_classes(df, actual_df):
        colors = ["first", "second", "third"]
        for col in df.columns:
            try:
                float_col = df[col].astype(float)
            except ValueError:
                continue  # for method and category cols

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
                    actual_df.at[index, col] = (
                        f'<td class="{colors[i]}">{actual_df.at[index, col]}</td>'
                    )

        return actual_df

    def add_top_3_classes_per_type(
        df, actual_df, category_col="category", include_3dgs=False
    ):
        colors = ["first", "second", "third"]
        for col in df.columns:
            try:
                float_col = df[col].astype(float)
            except ValueError:
                continue  # Skip non-numeric columns

            # Loop through each category type ('c', 'd')
            for category_type in df[category_col].unique():
                if category_type not in ["c", "d"]:
                    continue  # Skip unrelated categories

                # Filter rows by category
                filtered_indices = df[df[category_col] == category_type].index
                filtered_col = float_col[filtered_indices]

                # # Explicitly include the 3DGS-30K row in the filtered column
                # if include_3dgs:
                #     filtered_indices = filtered_indices.union(
                #         df[df["Method"].str.contains("3DGS-30K", na=False)].index
                #     )
                #     filtered_col = float_col[filtered_indices]

                if (
                    any(
                        keyword in col[1].lower()
                        for keyword in ["size", "lpips", "gauss", "b/g"]
                    )
                    or "rank" in col[0].lower()
                ):
                    top_3 = pd.Series(filtered_col.unique()).nsmallest(3)
                else:
                    top_3 = pd.Series(filtered_col.unique()).nlargest(3)

                # Assign "first", "second", "third" classes to the filtered rows
                for i, val in enumerate(top_3):
                    matching_indices = filtered_col[filtered_col == val].index
                    for index in matching_indices:
                        actual_df.at[index, col] = (
                            f'<td class="{colors[i]}">{actual_df.at[index, col]}</td>'
                        )

        return actual_df

    multi_col_df_copy = multi_col_df.copy()

    def numGaussians_to_k_Gauss(df):
        for (
            col
        ) in (
            df.columns
        ):  # Convert num gaussians col after ranking to enable string representation with ","
            if col[1] == "#Gaussians":  #
                df[col] /= 1000
                df[col] = df[col].apply(
                    lambda x: "{:,}".format(int(x)) if not pd.isna(x) else np.nan
                )

    def apply_dataset_names(df):
        df.columns = pd.MultiIndex.from_tuples(
            [
                (dataset_names[col[0]], col[1]) if col[0] in dataset_names else col
                for col in df.columns
            ]
        )

    numGaussians_to_k_Gauss(multi_col_df)
    multi_col_df = add_top_3_classes_per_type(
        multi_col_df_copy, multi_col_df.astype(str)
    ).replace(["nan", "NaN", "None"], "")

    def extract_method_name(html_string):
        # capture the text between the last </span> and </a>
        match = re.search(r"</span>([^<]+)</span>\s*</a>", html_string, re.IGNORECASE)
        if match:
            return match.group(1).strip()
        return None

    # parse dfs for latex
    for methods in ["compression", "densification"]:
        df = latex_dfs[methods]
        # Remove rows where rank is None
        latex_dfs[methods] = latex_dfs[methods][latex_dfs[methods]["Rank"].notna()]
        # Remove more rows
        latex_dfs[methods] = latex_dfs[methods].drop(columns=["category"])
        latex_dfs[methods] = latex_dfs[methods].drop(
            columns=[col for col in latex_dfs[methods].columns if col[1] == "b/G"]
        )
        if methods == "compression":
            latex_dfs[methods] = latex_dfs[methods].drop(
                columns=[
                    col for col in latex_dfs[methods].columns if col[1] == "#Gaussians"
                ]
            )
        else:
            latex_dfs[methods] = latex_dfs[methods].drop(
                columns=[
                    col for col in latex_dfs[methods].columns if col[1] == "Size [MB]"
                ]
            )
            latex_dfs[methods] = latex_dfs[methods].drop(
                columns=[
                    col
                    for col in latex_dfs[methods].columns
                    if col[0] == "SyntheticNeRF"
                ]
            )
        # Sort by the "Rank" column
        latex_dfs[methods] = latex_dfs[methods].sort_values(by=("Rank", ""))
        # Reset the index
        latex_dfs[methods] = latex_dfs[methods].reset_index(drop=True)
        df_copy = latex_dfs[methods].copy()
        numGaussians_to_k_Gauss(latex_dfs[methods])
        # Add top 3 classes to the dataframe
        latex_dfs[methods] = add_top_3_classes(
            df_copy, latex_dfs[methods].astype(str)
        ).replace(["nan", "NaN", "None"], "")
        # Rename all columns where the second entry in the column's name is '#Gaussians'
        latex_dfs[methods].columns = pd.MultiIndex.from_tuples(
            [
                (col[0], "k Gauss") if col[1] == "#Gaussians" else col
                for col in latex_dfs[methods].columns
            ]
        )
        # recover method name
        latex_dfs[methods]["Method"] = latex_dfs[methods]["Method"].apply(
            extract_method_name
        )
        apply_dataset_names(latex_dfs[methods])

    new_columns = []
    for col in multi_col_df.columns:  # rename #Gaussians
        if col[1] == "#Gaussians":
            new_col = (col[0], "k Gauss") + col[2:]
        else:
            new_col = col
        new_columns.append(new_col)

    # Set the new column names
    multi_col_df.columns = pd.MultiIndex.from_tuples(new_columns)

    apply_dataset_names(multi_col_df)

    html_string = multi_col_df.to_html(
        na_rep="",
        index=False,
        table_id="results",
        classes=["display", "cell-border"],
        justify="center",
        border=0,
        escape=False,
    )

    # Function to clean up nested <td> elements using regex
    def clean_nested_td(html):
        pattern = re.compile(r"<td><td([^>]*)>([^<]*)<\/td><\/td>")
        cleaned_html = pattern.sub(r"<td\1>\2</td>", html)
        return cleaned_html

    # Clean the HTML string
    cleaned_html_string = clean_nested_td(html_string)

    return (
        cleaned_html_string,
        ranks,
        groupcolors,
        rank_combinations,
        metric_formulas,
        method_categories,
        latex_dfs,
    )


def get_published_at(
    methods_files=["methods_compression.bib", "methods_densification.bib"]
):
    published_at = {}
    for methods_file in methods_files:
        with open(methods_file, encoding="utf-8") as bibtex_file:
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
                    elif "SIGGRAPH" in pub:
                        pub = "SIGGRAPH"
                    elif "ACM International Conference on Multimedia" in pub:
                        pub = "MM"
                    elif "Neural Information Processing Systems" in pub:
                        pub = "NeurIPS"
                    elif "International Conference on Learning Representations" in pub:
                        pub = "ICLR"
                    pub = pub + " '" + entry["year"][-2:]

                published_at[entry["ID"]] = pub

    return published_at


def load_methods_summaries(ranks, groupcolors):
    # Load the summaries of the methods
    summaries = []
    links = get_links()
    authors = get_authors()
    published_at = get_published_at()

    # sort here by rank to determine order of method summaries
    shortnames = get_shortnames(
        ["methods_compression.bib", "methods_densification.bib"]
    )

    # for now, only include ranked methods / uncomment to include unranked methods
    # shortnames_d = get_shortnames(["methods_densification.bib"])
    # shortnames_c = get_shortnames(["methods_compression.bib"])
    # for name in shortnames_d.values(): #also include non ranked methods
    #     if name not in ranks["d"]:
    #         ranks["d"][name] = 1000
    # for name in shortnames_c.values(): #also include non ranked methods
    #     if name not in ranks["c"]:
    #         ranks["c"][name] = 1000

    for category in ["c", "d"]:
        for shortname in ranks[category].keys():
            file = [key for key, value in shortnames.items() if value == shortname][
                0
            ] + ".md"
            if not os.path.exists(f"methods/{file}"):
                continue
            with open(f"methods/{file}", "r") as f:
                file_content = f.read()
                # markdown files, extarct title and summary
                title = file_content.split("\n")[0]
                if title.startswith("### "):
                    title = title[4:]
                elif title == "":
                    continue
                # include link to project page in title, if available
                if links[file.split(".")[0]] != "":
                    try:
                        color = groupcolors[shortnames[file.split(".")[0]]]
                    except KeyError:
                        color = "#ffffff"

                    class_str = (
                        "title-link" if category == "c" else "title-link densification"
                    )  # for different symbols
                    title = f'<a href="{links[file.split(".")[0]]}" target="_blank" class="{class_str}" style="--title-box-color: {color}">{title}</a>'
                summary = file_content.split("\n", 1)[1].strip()

                # insert color if applicable
                matches = re.finditer(r"<insert>(.*?)</insert>", summary)
                for match in matches:
                    shortname = match.group(1)
                    name = next(
                        (k for k, v in shortnames.items() if v == shortname), None
                    )
                    assert name is not None
                    color = groupcolors[shortname]
                    colorbox_text = f'<span><span class="text-color-box" style="background-color: {color};"></span><a href="#{name}" style="display: inline;">{shortname}</a></span>'

                    summary = summary.replace(match.group(0), colorbox_text)

                # get image path, webp, png or jpg
                if os.path.exists(
                    f"project-page/static/images/{file.split('.')[0]}_h250px.webp"
                ):
                    image = f"static/images/{file.split('.')[0]}_h250px.webp"
                else:
                    raise Exception(
                        f"images for {file.split('.')[0]} missing, please include an image and run preprocess_images.py first"
                    )

                # get width and height of image
                if image != "":
                    with Image.open(f"project-page/{image}") as img:
                        width, height = img.size

                author = authors[file.split(".")[0]]

                parts = author.split(" and ")
                if not "," in author:
                    formatted_authors = parts
                else:
                    formatted_authors = []
                    for part in parts:
                        # Split by comma and reverse the order
                        last, first = [p.strip() for p in part.split(",", 1)]
                        formatted_authors.append(f"{first} {last}")

                if len(formatted_authors) > 2:
                    author = (
                        ", ".join(formatted_authors[:-1])
                        + " and "
                        + formatted_authors[-1]
                    )
                else:
                    author = " and ".join(formatted_authors)

                summaries.append(
                    {
                        "name": file.split(".")[0],
                        "summary": summary,
                        "title": title,
                        "authors": author,
                        "image": image,
                        "imwidth": width,
                        "imheight": height,
                        "published_at": published_at[file.split(".")[0]],
                    }
                )
    return summaries


def get_plot_data(ranks):
    dfs = {}
    shortnames = get_shortnames(
        ["methods_compression.bib", "methods_densification.bib"]
    )
    shortnames_d = get_shortnames(
        ["methods_densification.bib"]
    )  # mark densification methdos for different representation in plots

    result_files = os.listdir("results")

    for file in result_files:
        # read csvs
        df = pd.read_csv(f"results/{file}", dtype={"Comment": str})
        df["Submethod"] = (
            df["Submethod"].astype("string").fillna("").replace("<NA>", "")
        )
        df["Shortname"] = df["Method"].apply(lambda x: shortnames[x])

        # filter out "Baseline" keyword from Submethod
        df["Submethod"] = df["Submethod"].str.replace("Baseline", " baseline")

        df["NewMethod"] = df["Shortname"] + df["Submethod"]

        # remove from df if [N/P] in comment
        df = df[~df["Comment"].str.contains(r"\[N/P\]", na=False)]

        # change Size [Bytes] to Size [MB] and round
        if "Size [Bytes]" in df.columns:
            df["Size [MB]"] = df["Size [Bytes]"] / 1000 / 1000
            df["Size [MB]"] = df["Size [MB]"].apply(lambda x: round(x, 1))
            df.drop(columns=["Size [Bytes]"], inplace=True)

        dfs[file.split(".")[0]] = df

    shortnames = sorted(shortnames.values())

    data = []
    for dataset in dataset_order:
        df = dfs[dataset]
        # sort by size to ensure correct lines between points
        df = df.sort_values(by="Size [MB]")

        psnr_groupData = {}
        ssim_groupData = {}
        lpips_groupData = {}

        for method in df.index:
            if psnr_groupData.get(df.loc[method, "Shortname"]) is None:
                psnr_groupData[df.loc[method, "Shortname"]] = {
                    "x": [],
                    "x2": [],
                    "y": [],
                    "text": [],
                }
            if ssim_groupData.get(df.loc[method, "Shortname"]) is None:
                ssim_groupData[df.loc[method, "Shortname"]] = {
                    "x": [],
                    "x2": [],
                    "y": [],
                    "text": [],
                }
            if lpips_groupData.get(df.loc[method, "Shortname"]) is None:
                lpips_groupData[df.loc[method, "Shortname"]] = {
                    "x": [],
                    "x2": [],
                    "y": [],
                    "text": [],
                }

            psnr_groupData[df.loc[method, "Shortname"]]["x"].append(
                df.loc[method, "Size [MB]"]
            )
            psnr_groupData[df.loc[method, "Shortname"]]["x2"].append(
                df.loc[method, "#Gaussians"]
            )
            psnr_groupData[df.loc[method, "Shortname"]]["y"].append(
                df.loc[method, "PSNR"]
            )
            psnr_groupData[df.loc[method, "Shortname"]]["text"].append(
                df.loc[method, "NewMethod"]
            )
            if df.loc[method, "Method"] in shortnames_d:
                psnr_groupData

            ssim_groupData[df.loc[method, "Shortname"]]["x"].append(
                df.loc[method, "Size [MB]"]
            )
            ssim_groupData[df.loc[method, "Shortname"]]["x2"].append(
                df.loc[method, "#Gaussians"]
            )
            ssim_groupData[df.loc[method, "Shortname"]]["y"].append(
                df.loc[method, "SSIM"]
            )
            ssim_groupData[df.loc[method, "Shortname"]]["text"].append(
                df.loc[method, "NewMethod"]
            )

            lpips_groupData[df.loc[method, "Shortname"]]["x"].append(
                df.loc[method, "Size [MB]"]
            )
            lpips_groupData[df.loc[method, "Shortname"]]["x2"].append(
                df.loc[method, "#Gaussians"]
            )
            lpips_groupData[df.loc[method, "Shortname"]]["y"].append(
                df.loc[method, "LPIPS"]
            )
            lpips_groupData[df.loc[method, "Shortname"]]["text"].append(
                df.loc[method, "NewMethod"]
            )

        data.append(
            {
                "plot1": {
                    "title": f"<b>{dataset_names[dataset]}</b>",  #: PSNR / Size
                    "xaxis": "Size (MB)",
                    "yaxis": "PSNR",
                    "groupData": psnr_groupData,
                    "lines": [],
                    "lineHeight": org_3dgs[dataset][0],
                },
                "plot2": {
                    "title": f"<b>{dataset_names[dataset]}</b>",  #: SSIM / Size
                    "xaxis": "Size (MB)",
                    "yaxis": "SSIM",
                    "groupData": ssim_groupData,
                    "lines": [],
                    "lineHeight": org_3dgs[dataset][1],
                },
                "plot3": {
                    "title": f"<b>{dataset_names[dataset]}</b>",  #: LPIPS / Size
                    "xaxis": "Size (MB)",
                    "yaxis": "LPIPS",
                    "groupData": lpips_groupData,
                    "lines": [],
                    "lineHeight": org_3dgs[dataset][2],
                },
            }
        )

    group_links = {}
    densification_methods = {}
    shortnames = get_shortnames(
        ["methods_compression.bib", "methods_densification.bib"]
    )
    for method in shortnames:
        group_links[shortnames[method]] = "#" + method
        if method in shortnames_d:
            densification_methods[shortnames_d[method]] = (
                1  # differentiate c and d methdos in js
            )

    checkbox_states = {}
    for method in shortnames.values():
        if method in ["3DGS-30K", "Scaffold-GS", "AtomGS", "GaussianPro"]:
            checkbox_states[method] = False
        else:
            checkbox_states[method] = True

    return data, group_links, checkbox_states, densification_methods


if __name__ == "__main__":
    (
        results_table,
        ranks,
        groupcolors,
        rank_combinations,
        metric_formulas,
        method_categories,
        _,
    ) = combine_tables_to_html()
    summaries = load_methods_summaries(ranks, groupcolors)
    plot_data, group_links, checkbox_states, densification_methods = get_plot_data(
        ranks
    )

    # Pfad zu deinem Template-Ordner
    file_loader = FileSystemLoader("project-page")
    env = Environment(loader=file_loader)

    # Lade das Template
    template = env.get_template("index_template.html")

    # Daten, die in das Template eingefügt werden sollen
    data = {
        "results_table": results_table,
        "summaries": summaries,
        "plot_data": json.dumps(plot_data),
        "group_links": json.dumps(group_links),
        "checkbox_states": json.dumps(checkbox_states),
        "groupcolors": json.dumps(groupcolors),
        "rank_combinations": json.dumps(rank_combinations),
        "metric_formulas": json.dumps(metric_formulas),
        "method_categories": json.dumps(method_categories),
        "densification_methods": json.dumps(densification_methods),
    }

    # Render das Template mit den Daten
    output = template.render(data)

    # Speichere das gerenderte HTML in einer Datei
    with open("project-page/index.html", "w", encoding="utf-8") as f:
        f.write(output)
