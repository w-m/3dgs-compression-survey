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

Authors are kindly requested to upload their per-scene results in a designated folder within their GitHub repository. This ensures accurate data retrieval and allows for consistent and fair comparisons. The expected folder structure is:

```
results
├── DeepBlending
│   ├── drjohnson.csv
│   └── playroom.csv
├── MipNeRF360
│   ├── bicycle.csv
│   ├── bonsai.csv
│   ├── counter.csv
│   ├── flowers.csv
│   ├── garden.csv
│   ├── kitchen.csv
│   ├── room.csv
│   ├── stump.csv
│   └── treehill.csv
├── SyntheticNeRF
│   ├── chair.csv
│   ├── drums.csv
│   ├── ficus.csv
│   ├── hotdog.csv
│   ├── lego.csv 
│   ├── materials.csv
│   ├── mic.csv
│   └── ship.csv
└── TanksAndTemples
    ├── train.csv
    └── truck.csv
```

The folder should include all datasets on which your method was evaluated and cover all scenes specified in the folder structure.

Each CSV file should be structured as follows:

```
Submethod,PSNR,SSIM,LPIPS,Size [Bytes],#Gaussians
Baseline,xx.xx,0.xxx,0.xxx,xxxxxxxx,xxxxxxxx
-SubmethodName,xx.xx,0.xxx,0.xxx,xxxxxxxx,xxxxxxxx
,xx.xx,0.xxx,0.xxx,xxxxxxxx,xxxxxxxx
,xx.xx,0.xxx,0.xxx,xxxxxxxx,xxxxxxxx
,xx.xx,0.xxx,0.xxx,xxxxxxxx,xxxxxxxx

```

Include up to two consistent submethod names for your results across all files to ensure they appear in the survey table. These names will then be concatenated with the name of your approach in the table. If you prefer only the name of your approach to be displayed in the table, you can use "Baseline" as a submethod name for those results. Results without a submethod name will only be displayed in the plots.

You can view an example [here](https://github.com/fraunhoferhhi/Self-Organizing-Gaussians/tree/main/results)

### Important: 3DGS testing conventions

Authors are required to adhere to the testing conventions established in the original [3DGS project](https://github.com/graphdeco-inria/gaussian-splatting). Specifically, this includes:

- Using all 9 scenes from the MipNeRF360 dataset, including "flowers" and "treehill".
- Evaluating images at full resolution up to a maximum width of 1600px. Larger test images should be downscaled to a width of 1600px (which is only applicable for MipNeRF360).
- For the 3 COLMAP datasets (Tanks and Temples, Deep Blending, MipNeRF360), use every 8th image for testing. Concretly, the test images are those where ```idx % 8 == 0```.
- For the Blender dataset (SyntheticNeRF), follow the predefined train/eval split.


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

## Citation

If you use our survey in your research, please cite our work. You can use the following BibTeX entry:

```bibtex
@misc{3DGSzip2024,
    title={3DGS.zip: A survey on 3D Gaussian Splatting Compression Methods}, 
    author={Milena T. Bagdasarian and Paul Knoll and Florian Barthel and Anna Hilsmann and 
            Peter Eisert and Wieland Morgenstern},
    year={2024},
    eprint={2407.09510},
    archivePrefix={arXiv},
    primaryClass={cs.CV},
    url={https://arxiv.org/abs/2407.09510}, 
}
```
