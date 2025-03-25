#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.12"
# dependencies = [
#     "click",
#     "matplotlib",
#     "natsort",
#     "numpy",
#     "pandas",
#     "plyfile",
#     "seaborn",
# ]
# ///

"""
This script generates visualizations from a 3DGS .ply file:
- Correlation heatmaps showing relationships between various columns
- Histograms displaying the distribution of different attributes

These graphs are used in the paper version of "3DGS.zip: A survey on 3D Gaussian Splatting Compression Methods".

Usage:
    - `./heatmap_hist_plot.py --input-file PATH_TO_PLY_FILE`
"""

from plyfile import PlyData
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

import click
import matplotlib
import natsort

matplotlib.rcParams['pdf.fonttype'] = 42
matplotlib.rcParams['ps.fonttype'] = 42

import seaborn as sns
sns.set_theme(style="whitegrid")


def load_ply_data(input_file):
    """Load PLY data and convert to pandas DataFrame."""
    print(f"Loading data from {input_file}")
    data = PlyData.read(input_file)
    vertex_data = data["vertex"]
    return pd.DataFrame(vertex_data.data)


def create_relevant_cols_corr(df):
    """Create correlation heatmap for relevant columns."""
    non_normal_cols = [
        "x", "y", "z", "scale_0", "scale_1", "scale_2", 
        "rot_0", "rot_1", "rot_2", "rot_3", "opacity", 
        "f_dc_0", "f_dc_1", "f_dc_2",
    ]
    
    dfnn = df[non_normal_cols]
    corr_nn = dfnn.corr()
    
    plt.figure()
    sns.heatmap(
        corr_nn,
        xticklabels=corr_nn.columns.values,
        yticklabels=corr_nn.columns.values,
        vmin=-1.0,
        vmax=1.0,
        cmap="vlag",
    )
    plt.gcf().set_size_inches(6, 6)
    plt.subplots_adjust(hspace=None)
    plt.subplots_adjust(left=0, right=1, top=1, bottom=0)
    plt.savefig("relevant_cols_corr.pdf", bbox_inches="tight", pad_inches=0)
    plt.close()


def create_opacity_scale_hist(df):
    """Create histogram for opacity and scale columns."""
    text_hist_cols = ["opacity", "scale_0"]
    
    dfins = df[text_hist_cols].hist(bins=50, layout=(1, 2), figsize=(6, 4), sharey=True)
    # Modify y-axis to show the amount in thousands ("k")
    for ax in dfins.flatten():
        ax.yaxis.set_major_formatter(
            plt.FuncFormatter(lambda x, loc: "{:,}k".format(int(x / 1000)))
        )
    plt.margins(0)
    plt.subplots_adjust(left=0, right=1, top=1, bottom=0)
    # plt.subplots_adjust(wspace=0.5)
    # plt.gcf().set_size_inches(8, 4)
    plt.savefig("opacity_scale_hist.pdf", bbox_inches="tight", pad_inches=0)
    plt.close()


def create_most_cols_hist(df):
    """Create histograms for most columns."""
    appendix_hist_cols = [
        "x", "y", "z", "scale_0", "scale_1", "scale_2", 
        "rot_0", "rot_1", "rot_2", "rot_3", "opacity", 
        "f_dc_0", "f_dc_1", "f_dc_2", 
        "f_rest_0", "f_rest_1", "f_rest_2", "f_rest_3", "f_rest_4", 
        "f_rest_5", "f_rest_6", "f_rest_7", "f_rest_8", "f_rest_9",
    ]
    
    dfins = df[appendix_hist_cols].hist(
        bins=50, layout=(8, 3), figsize=(12, 18), sharey=True
    )
    # Modify y-axis to show the amount in millions ("M")
    for ax in dfins.flatten():
        ax.yaxis.set_major_formatter(
            plt.FuncFormatter(lambda x, loc: "{:,}M".format(int(x / 1_000_000)))
        )
    plt.subplots_adjust(hspace=0.6)
    plt.margins(0)
    plt.subplots_adjust(left=0, right=1, top=1, bottom=0)
    plt.savefig("most_cols_hist.pdf", bbox_inches="tight", pad_inches=0)
    plt.close()


def create_all_cols_corr(df):
    """Create correlation heatmap for all columns."""
    non_normal_cols = [
        "x", "y", "z", "scale_0", "scale_1", "scale_2", 
        "rot_0", "rot_1", "rot_2", "rot_3", "opacity", 
        "f_dc_0", "f_dc_1", "f_dc_2",
    ]
    
    sh_ac_cols = [f"f_rest_{i + j}" for i in range(15) for j in [0, 15, 30]]
    non_normal_cols.extend(sh_ac_cols)
    
    dfnn = df[non_normal_cols]
    corr_nn = dfnn.corr()
    
    plt.figure()
    sns.heatmap(
        corr_nn,
        xticklabels=corr_nn.columns.values,
        yticklabels=corr_nn.columns.values,
        vmin=-1.0,
        vmax=1.0,
        cmap="vlag",
    )
    plt.subplots_adjust(left=0, right=1, top=1, bottom=0)
    plt.gcf().set_size_inches(16, 16)
    plt.savefig("all_cols_corr.pdf", bbox_inches="tight", pad_inches=0)
    plt.close()


@click.command(help="Generate visualizations for 3D Gaussian Splatting point cloud data.")
@click.option('--input-file', '-i', required=True, 
              help='Path to the PLY file containing Gaussian Splatting point cloud data.')
def main(input_file):
    """Main function to orchestrate the visualization creation process."""
    df = load_ply_data(input_file)
    
    create_relevant_cols_corr(df)
    create_opacity_scale_hist(df)
    create_most_cols_hist(df)
    create_all_cols_corr(df)
    
    print("All visualizations have been successfully created.")


if __name__ == "__main__":
    main()


