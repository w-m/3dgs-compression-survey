import os
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.ticker import LogLocator, ScalarFormatter

# Import necessary functions and color lists from build_html.py
from build_html import (
    get_shortnames,
    org_3dgs,
    dataset_names,
    dataset_order,
    colors,      # List of colors for compression methods
    colors_d     # List of colors for densification methods
)

# Ensure the 'plots' directory exists
os.makedirs('plots', exist_ok=True)

def read_and_process_data():
    dfs = {}
    # Get method shortnames from the bibliography files
    shortnames = get_shortnames(["methods_compression.bib", "methods_densification.bib"])
    shortnames_d = get_shortnames(["methods_densification.bib"])  # Densification methods
    shortnames_c = get_shortnames(["methods_compression.bib"])

    result_files = os.listdir('results')

    for file in result_files:
        if not file.endswith('.csv'):
            continue  # Skip non-CSV files
        file_path = os.path.join('results', file)
        try:
            df = pd.read_csv(file_path)
        except Exception as e:
            print(f"Error reading {file_path}: {e}")
            continue

        # Process 'Submethod' column
        df['Submethod'] = df['Submethod'].astype('string').fillna('').replace('<NA>', '')
        df['Submethod'] = df['Submethod'].str.replace('Baseline', ' baseline', regex=False)

        # Map 'Method' to 'Shortname'
        df["Shortname"] = df["Method"].map(shortnames).fillna(df["Method"])

        # Create 'NewMethod' column
        df["NewMethod"] = df["Shortname"] + df["Submethod"]

        # Remove entries with [N/P] in 'Comment'
        if 'Comment' in df.columns:
            df = df[~df['Comment'].str.contains(r'\[N/P\]', na=False)]

        # Convert 'Size [Bytes]' to 'Size [MB]' if the column exists
        if "Size [Bytes]" in df.columns:
            df["Size [MB]"] = (df["Size [Bytes]"] / (1024 * 1024)).round(1)
            df.drop(columns=["Size [Bytes]"], inplace=True)

        # Store the processed DataFrame
        dataset_key = os.path.splitext(file)[0]
        dfs[dataset_key] = df

    return dfs, shortnames, shortnames_d, shortnames_c

# Read and process the data
dfs, shortnames, shortnames_d, shortnames_c = read_and_process_data()

metrics = ['PSNR', 'SSIM', 'LPIPS']

# Define method types with their corresponding data subsets and plot configurations
method_types = [
    {
        'type': 'densification',
        'data_subset': lambda df: df[df['Method'].isin(shortnames_d.keys())],
        'x_label': '#Gaussians',
        'x_column': '#Gaussians',
        'filename_suffix': 'compaction'
    },
    {
        'type': 'compression',
        'data_subset': lambda df: df[~df['Method'].isin(shortnames_d.keys())],
        'x_label': 'Size [MB]',
        'x_column': 'Size [MB]',
        'filename_suffix': 'compression'
    }
]

# Initialize dictionaries for color mapping
groupcolors = {}            # Maps shortnames to colors
method_categories_dict = {} # Optional: If you use this elsewhere

# Assign colors to compression methods
for name, shortname in shortnames_c.items():
    if shortname not in ["F-3DGS"]:
        if not colors:
            print("Warning: Ran out of colors for compression methods. Some methods will use default colors.")
            break
        groupcolors[shortname] = colors.pop(0)
    method_categories_dict[name] = "c"

# Assign colors to densification methods
for name, shortname in shortnames_d.items():
    if shortname not in ["F-3DGS"]:
        if not colors_d:
            print("Warning: Ran out of colors for densification methods. Some methods will use default colors.")
            break
        groupcolors[shortname] = colors_d.pop(0)
    method_categories_dict[name] = "d"

for dataset in dataset_order:
    if dataset not in dfs:
        print(f'Dataset {dataset} not found in results.')
        continue

    df = dfs[dataset]

    # Sort DataFrame by 'Size [MB]' or '#Gaussians' for consistency, if available
    if 'Size [MB]' in df.columns:
        df = df.sort_values(by="Size [MB]")
    elif '#Gaussians' in df.columns:
        df = df.sort_values(by="#Gaussians")

    for metric in metrics:
        for method_type in method_types:
            subset_df = method_type['data_subset'](df)

            if subset_df.empty:
                print(f"No data for {method_type['type']} methods in dataset {dataset}.")
                continue

            plt.figure(figsize=(6.67, 4))
            for method in subset_df['Shortname'].unique():
                method_data = subset_df[subset_df['Shortname'] == method]
                x = method_data[method_type['x_column']]
                y = method_data[metric]
                
                # Retrieve the color for the current method, default to 'C0' if not found
                color = groupcolors.get(method, 'C0')

                if method_type["type"] == "compression":
                    marker = "^"
                else:
                    marker = "o"
                if method_type["type"] == "compression":
                    plt.plot(x, y, marker=marker, label=method, color=color)
                else:
                    # plt.scatter(x, y, label=method, color=color, marker=marker)
                    # Plot the lines with transparency
                    plt.plot(x, y, color=color, alpha=0.2)  # Lines with transparency

                    # Plot the markers without transparency
                    plt.scatter(x, y, label=method, color=color, marker=marker)  # Markers without transparency

            plt.xlabel(method_type['x_label'])
            plt.ylabel(metric)
            title_type = "Compaction Methods" if method_type['type'] == 'densification' else "Compression Methods"
            plt.title(f"{dataset_names.get(dataset, dataset)} - {title_type} - {metric} vs {method_type['x_label']}")

            # Invert y-axis for LPIPS metric
            if metric == 'LPIPS':
                plt.gca().invert_yaxis()

            # Add horizontal line for original 3DGS value, if it exists and is valid
            metric_index = metrics.index(metric)
            if dataset in org_3dgs and org_3dgs[dataset][metric_index] is not None and method_type["type"] == "compression":
                try:
                    lineHeight = float(org_3dgs[dataset][metric_index])
                    # plt.axhline(y=lineHeight, color='darkgrey', linestyle='--', label='Original 3DGS')
                    plt.axhline(y=lineHeight, color='black', linestyle='--', linewidth=1, label='3DGS-30K', dashes=(5, 5))

                except ValueError:
                    print(f"Invalid 3DGS value for {dataset} and metric {metric}.")
            else:
                try:
                    lineHeight = float(org_3dgs[dataset][metric_index])
                    gaussians = org_3dgs[dataset][-1]
                    plt.plot(gaussians, lineHeight, marker='x', label='3DGS-30K', color="darkgrey", markersize=10, markeredgewidth=2, markeredgecolor='black')
                except Exception:
                    print(f"Invalid 3DGS value for {dataset} and metric {metric}.")
            
            if method_type["type"] == "compression":
                plt.xscale('log')
                # Enable minor ticks
                plt.minorticks_on()

                # Set up major and minor tick locators
                plt.gca().xaxis.set_major_locator(LogLocator(base=10.0))  # Major ticks at powers of 10
                plt.gca().xaxis.set_minor_locator(LogLocator(base=10.0, subs=[2, 3, 5, 7]))  # Minor ticks at 2, 3, 5, 7

                # Set formatters for major and minor ticks
                plt.gca().xaxis.set_major_formatter(ScalarFormatter())  # Automatically labels major ticks
                plt.gca().xaxis.set_minor_formatter(ScalarFormatter())  # Automatically labels minor ticks

            plt.tight_layout()
            plt.grid(True)

            # Save the plot with a descriptive filename
            plot_filename = f"{dataset}_{method_type['filename_suffix']}_{metric}.pdf"

            plot_path = os.path.join('plots', plot_filename)
            plt.savefig(plot_path, bbox_inches='tight')
            print(f"Saved plot: {plot_path}")
            ########################################################################
            # plt.legend()
            plt.legend(loc='upper left', bbox_to_anchor=(1, 1))
            # plt.legend(loc='best')

            plot_filename = f"{dataset}_{method_type['filename_suffix']}_{metric}_legend.pdf"

            plot_path = os.path.join('plots', plot_filename)
            plt.savefig(plot_path, bbox_inches='tight')
            print(f"Saved plot: {plot_path}")
            ########################################################################
            plt.legend(loc='upper center', bbox_to_anchor=(0.5, -0.2), ncol=4)

            plot_filename = f"{dataset}_{method_type['filename_suffix']}_{metric}_legend_h.pdf"

            plot_path = os.path.join('plots', plot_filename)
            plt.savefig(plot_path, bbox_inches='tight')
            print(f"Saved plot: {plot_path}")
            ########################################################################
            plt.close()
