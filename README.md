# 3DGS.zip: A survey on 3D Gaussian Splatting Compression Methods
This repository contains a comprehensive survey of 3D Gaussian Splatting (3DGS) compression methods. You can view the full survey table and comparison plots at [w-m.github.io/3dgs-compression-survey/](https://w-m.github.io/3dgs-compression-survey/).

## Installation
To run the scripts in this repository, ensure you have all necessary dependencies installed. You can install them using the following command:

`pip install -r requirements.txt`

## Building the Site
To build the site, use the following command: 

`python data_extraction/build_html.py`

This scrips also runs automatically to rebuild the site whenever changes are pushed to the main branch.

## Fetching Results
You can fetch the results automatically by running: 

`python data_extraction/data_extraction.py`

This script attempts to fetch data from the relevant papers and update the tables in the `results` folder. To add a new paper, create an entry in `data_extraction/data_source.yaml`. 

## Including your own Results

It is recommended that authors include their results in a separate folder within their GitHub repository to ensure correct data retrieval. The expected folder structure is:

```
results
├── DeepBlending.csv
├── MipNeRF360.csv
├── SyntheticNeRF.csv
├── TanksAndTemples.csv
```

Please include all datasets on which your method was evaluated in the results folder.

Each CSV file should be structured as follows:

```
Submethod,PSNR,SSIM,LPIPS,Size [Bytes]
Baseline,xx.xx,0.xxx,0.xxx,xxxxxxxx
-SubmethodName,xx.xx,0.xxx,0.xxx,xxxxxxxx
,xx.xx,0.xxx,0.xxx,xxxxxxxx
,xx.xx,0.xxx,0.xxx,xxxxxxxx
,xx.xx,0.xxx,0.xxx,xxxxxxxx

```

Include up to two consistent submethod names for your results across all files to ensure they appear in the survey table. These names will then be concatenated with the name of your approach in the table. If you prefer only the name of your approach to be displayed in the table, you can use "Baseline" as a submethod name for those results. Results without a submethod name will only be displayed in the plots.

You can view an example [here](https://github.com/fraunhoferhhi/Self-Organizing-Gaussians/tree/main/results)

## LaTeX Table

An up-to-date LaTeX version of the survey table can be found here [here](https://github.com/w-m/3dgs-compression-survey/blob/main/data_extraction/latex/3dgs_table.tex). Feel free to copy a line from the table into your research if you want to compare to the approach. Should you wish to copy the whole table you might need the following packages and definitions in your LaTeX preamble:
```
\usepackage{booktabs}
\usepackage[table]{xcolor}
% colors for table
\definecolor{lightred}{HTML}{FF9999}
\definecolor{lightyellow}{HTML}{FFFF99}
\definecolor{lightorange}{HTML}{FFCC99}
\usepackage{makecell}
\usepackage{adjustbox}
% make text the same size even when its bold in a table
\newsavebox\CBox
\def\textBF#1{\sbox\CBox{#1}\resizebox{\wd\CBox}{\ht\CBox}{\textbf{#1}}}
```
