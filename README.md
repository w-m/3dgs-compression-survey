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

Please ensure that the PSNR results are reported with a precision of at least two decimal places, and that SSIM and LPIPS results are reported with a precision of at least three decimal places. Authors are encouraged to provide results with full precision, as these will be rounded before inclusion in our survey.

Include up to two consistent submethod names for your results across all files to ensure they appear in the survey table. These names will then be concatenated with the name of your approach in the table. If the submethod specifier should be separated from the method name with a space, make sure to include that space in front of the submethod name. If you prefer only the name of your approach to be displayed in the table, you can use "Baseline" as a submethod name for those results. Results without a submethod name will only be displayed in the plots.

You can view an example [here](https://github.com/fraunhoferhhi/Self-Organizing-Gaussians/tree/main/results).

### Important: 3DGS testing conventions

Authors are required to adhere to the testing conventions established in the original [3DGS project](https://github.com/graphdeco-inria/gaussian-splatting). Specifically, this includes:

- Using all 9 scenes from the MipNeRF360 dataset, including the [extra scenes](https://storage.googleapis.com/gresearch/refraw360/360_extra_scenes.zip) "flowers" and "treehill".
- Evaluating images at full resolution up to a maximum side length of 1600px. Larger test images should be downscaled so that the longest dimension equals 1600px (applicable only to MipNeRF360). Make sure the resizing aligns with 3DGS, which applies the standard PIL ```.resize()``` method with bicubic resampling.  
- For the 3 COLMAP datasets (Tanks and Temples, Deep Blending, MipNeRF360), use every 8th image for testing. Concretly, the test images are those where ```idx % 8 == 0```.
- For the Blender dataset (SyntheticNeRF), follow the predefined train/eval split.


## LaTeX Table

An up-to-date LaTeX version of the survey table can be found [here](https://github.com/w-m/3dgs-compression-survey/blob/main/data_extraction/latex/3dgs_table.tex). Feel free to copy a line from the table into your research if you want to compare to the approach. Should you wish to copy the whole table you might need the following packages and definitions in your LaTeX preamble:
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
@article{3DGSzip2024,
    title={3DGS.zip: A survey on 3D Gaussian Splatting Compression Methods}, 
    author={Milena T. Bagdasarian and Paul Knoll and Yi-Hsin Li and Florian Barthel and Anna Hilsmann and Peter Eisert and Wieland Morgenstern},
    journal={arXiv preprint arXiv:2407.09510},
    year={2024}, 
} 
```

## Updates
- 2025-02-25: added GaussianSpa
- 2025-02-25: Added HAC++
- 2025-02-25: Added FCGS
- 2025-02-10: Removed IGS as the publication is withdrawn
- 2025-02-05: Added CodecGS
- 2024-11-21: Added ContextGS
- 2024-11-07: Added CompGS
- 2024-11-05: Updated [arXiv](https://arxiv.org/abs/2407.09510) version with compression and compaction methods and a fundamentals of 3DGS compression
- 2024-10-21: Officially rename "densification" methods to "compaction" methods on website to align with survey paper
- 2024-10-17: Add GaussiansPro, AtomGS and Taming3DGS to densification/compaction methods
- 2024-10-14: Add MesonGS to compression methods
- 2024-09-30: Add densification methods to survey
- 2024-09-17: Updated Morgenstern et al. results and reverted HAC results because of [confusion about testing conventions](https://github.com/YihangChen-ee/HAC/issues/14)
- 2024-09-05: Update Scaffold-GS MipNeRF-360 results to include all 9 scenes
- 2024-08-27: Add IGS method to survey
- 2024-08-26: Add gsplat method to survey
- 2024-08-14: Adaptive ranks based on attribute and dataset selection
- 2024-08-12: New plots to show metrics over number of Gaussians instead of model size
- 2024-08-08: Add checkboxes to select metrics and datasets to be shown in table
- 2024-08-07: Include number of Gaussians in survey, include bits per Gaussian in table
- 2024-08-02: Show conferences of published papers
- 2024-06-19: New rank calculation with all available datasets
- 2024-06-17: Include ranks of methods
- 2024-06-17: Initial publication of survey on [arXiv](https://arxiv.org/abs/2407.09510)
- 2024-06-13: Add plots of metrics over model size
- 2024-06-10: First draft of survey page with interactive table


<!-- - 2024-08-22: Released pre-trained, [compressed scenes](https://github.com/fraunhoferhhi/Self-Organizing-Gaussians/releases/tag/eccv-2024-data)
- 2024-07-09: Project website updated with TLDR, contributions, insights and comparison to concurrent methods
- 2024-07-01: Our work was accepted at **ECCV 2024** 🥳
- 2024-06-13: Training code available
- 2024-05-14: Improved compression scores! New results for paper v2 available on the [project website](https://fraunhoferhhi.github.io/Self-Organizing-Gaussians/)
- 2024-05-02: Revised [paper v2](https://arxiv.org/pdf/2312.13299) on arXiv: Added compression of spherical harmonics, updated compression method with improved results (all attributes compressed with JPEG XL now), added qualitative comparison of additional scenes, moved compression explanation and comparison to main paper, added comparison with "Making Gaussian Splats smaller".
- 2024-02-22: The code for the sorting algorithm is now available at [fraunhoferhhi/PLAS](https://github.com/fraunhoferhhi/PLAS)
- 2024-02-21: Video comparisons for different scenes available on the [project website](https://fraunhoferhhi.github.io/Self-Organizing-Gaussians/)
- 2023-12-19: Preprint available on [arXiv](https://arxiv.org/abs/2312.13299) -->
