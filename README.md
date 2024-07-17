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

It is recommended to the authors to include their results in their Github repository, to ensure that the data is fetched correctly. You can view the expected format [here](https://github.com/fraunhoferhhi/Self-Organizing-Gaussians/tree/main/results). Please provide a submethod name for up to two results per dataset to be displayed in the survey table. Results without a submethod name will only be shown in the plots. Use the keyword "Baseline" to ensure only the name of your approach is shown in the table for these results.