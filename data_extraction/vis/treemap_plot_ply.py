#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.12"
# dependencies = [
# "kaleido",
#     "matplotlib",
#     "mathjax",
#     "numpy",
#     "plotly",
# ]
# ///

# This script creates a treemap that shows the detailed memory allocation of the 'Truck' scene in 3D Gaussian Splatting, .ply format.

# It's LLM-written for a quick visualisation, don't expect the comments to be particularly useful or the code to be approachable.

# Usage:
#    `./treemap_plot_ply.py`


from collections import defaultdict
from matplotlib import cm
import numpy as np
import plotly.graph_objects as go
import plotly.io as pio

import re

pio.kaleido.scope.mathjax = None

# Define labels and parents for the full treemap structure
labels = [
    "Truck",
    "Coordinates", "x", "y", "z",
    "Normals [Unused]", "nx", "ny", "nz",
    "Colors",
    "SH Degree 0", "f_dc_0", "f_dc_1", "f_dc_2",
    "View Dependent",
    "SH Degree 1",  # SH Degree nodes under View Dependent
    "SH Degree 2",
    "SH Degree 3",
    "Opacity",
    "Scale", "scale_0", "scale_1", "scale_2",
    "Rotation", "rot_0", "rot_1", "rot_2", "rot_3"
]

# Append f_rest_* labels grouped by degree
f_rest_labels = []
parents = [
    "", "Truck", "Coordinates", "Coordinates", "Coordinates",
    "Truck", "Normals [Unused]", "Normals [Unused]", "Normals [Unused]",
    "Truck",
    "Colors", "SH Degree 0", "SH Degree 0", "SH Degree 0",
    "Colors",
    # Parents for Degree nodes
    "View Dependent", "View Dependent", "View Dependent",
    "Truck",
    "Truck", "Scale", "Scale", "Scale",
    "Truck", "Rotation", "Rotation", "Rotation", "Rotation"
]

# Adding Degree nodes and their f_rest_* children
# Degree 1: f_rest_0 to f_rest_8
for i in range(9):
    label = f"f_rest_{i}"
    labels.append(label)
    parents.append("SH Degree 1")
    f_rest_labels.append(label)

# Degree 2: f_rest_9 to f_rest_23
for i in range(9, 24):
    label = f"f_rest_{i}"
    labels.append(label)
    parents.append("SH Degree 2")
    f_rest_labels.append(label)

# Degree 3: f_rest_24 to f_rest_44
for i in range(24, 45):
    label = f"f_rest_{i}"
    labels.append(label)
    parents.append("SH Degree 3")
    f_rest_labels.append(label)

# Keep a copy of original labels
original_labels = labels.copy()

# Create a mapping from original label to index
original_label_to_index = {label: idx for idx, label in enumerate(original_labels)}

# Build a tree structure to map each node to its children
children = defaultdict(list)
for idx, (label, parent) in enumerate(zip(labels, parents)):
    if parent != '':
        children[parent].append(label)

# Initialize sizes array
sizes = [0] * len(labels)

# Find parent and leaf nodes
non_leaf_nodes = set(children.keys())
leaf_nodes = [label for label in labels if label not in non_leaf_nodes]

# Assign size to leaf nodes (2541226 elements * 4 bytes per entry)
leaf_size = 2541226 * 4  # Size in bytes
for leaf_label in leaf_nodes:
    idx = original_label_to_index[leaf_label]
    sizes[idx] = leaf_size

# Function to compute sizes recursively
def compute_size(label):
    idx = original_label_to_index[label]
    if sizes[idx] != 0:
        return sizes[idx]
    else:
        total_size = sum(compute_size(child_label) for child_label in children[label])
        sizes[idx] = total_size
        return total_size

# Compute sizes for all labels
for label in labels:
    compute_size(label)

# Convert sizes to MB for values
values_in_MB = [size / 1_000_000 for size in sizes]

# Create a 'text' array to include size for child nodes and empty for parent nodes
text = []
for idx, label in enumerate(labels):
    original_label = original_labels[idx]
    value = values_in_MB[idx]
    if original_label in non_leaf_nodes:
        # Parent node: Update label to include size
        labels[idx] = f"{label} - {value:.2f} MB"
        text.append('')
    else:
        # Child node: Text includes size with line break
        text.append(f"{value:.2f} MB")

# Update parents to match the updated labels
for idx, parent in enumerate(parents):
    if parent != '':
        parent_idx = original_label_to_index[parent]
        parents[idx] = labels[parent_idx]

# Rebuild the label_to_index mapping with updated labels
label_to_index = {label: idx for idx, label in enumerate(labels)}

# Define group labels
group_labels = {
    'rotation': ['Rotation', 'rot_0', 'rot_1', 'rot_2', 'rot_3'],
    'position': ['Coordinates', 'x', 'y', 'z'],
    'scale': ['Scale', 'scale_0', 'scale_1', 'scale_2'],
    'opacity': ['Opacity'],
    'f_dc': ['f_dc_0', 'f_dc_1', 'f_dc_2'],
    'f_rest': f_rest_labels,  # f_rest_0 to f_rest_44
    'normals': ['Normals [Unused]', 'nx', 'ny', 'nz'],
    'others': ['Truck', 'Colors', 'SH Degree 0', 'View Dependent', 'SH Degree 1', 'SH Degree 2', 'SH Degree 3'],
}

# Define group colors
group_colors = {
    'rotation': '#d5a6bd',
    'position': '#a4c2f4',
    'scale': '#b6d7a8',
    'opacity': '#eeeeee',
    'f_dc': '#f9cb9c',
    'f_rest': '#ea9999',
    'normals': '#cccccc',
    'others': '#999999',
}

# Function to convert hex color to rgba
def hex_to_rgba(hex_color):
    r, g, b = tuple(int(hex_color.lstrip('#')[i:i+2], 16) for i in (0, 2 ,4))
    return f'rgba({r}, {g}, {b}, 1.0)'

# Function to adjust luminance
def adjust_luminance(hex_color, factor):
    """Adjusts the luminance of a hex color by multiplying the HSL lightness by factor."""
    import colorsys
    # Convert hex to RGB
    r, g, b = tuple(int(hex_color.lstrip('#')[i:i+2], 16)/255.0 for i in (0, 2 ,4))
    # Convert RGB to HLS
    h, l, s = colorsys.rgb_to_hls(r, g, b)
    # Adjust luminance
    l = max(0, min(1, l * factor))
    # Convert back to RGB
    r_new, g_new, b_new = colorsys.hls_to_rgb(h, l, s)
    # Convert RGB to hex
    r_int, g_int, b_int = int(r_new * 255), int(g_new * 255), int(b_new * 255)
    return f'#{r_int:02x}{g_int:02x}{b_int:02x}'

# Function to get colors for a group
def get_group_colors(indices, group_name):
    color_def = group_colors.get(group_name, 'viridis')
    num_colors = len(indices)
    if isinstance(color_def, str) and color_def.startswith('#'):
        # It's a hex color
        if num_colors == 1:
            # Only one color needed
            colors = [hex_to_rgba(color_def)]
        else:
            # Generate variations in luminance
            factors = np.linspace(0.9, 1.1, num_colors)
            colors = [hex_to_rgba(adjust_luminance(color_def, factor)) for factor in factors]
    elif isinstance(color_def, str):
        # Assume it's a colormap name
        cmap = cm.get_cmap(color_def, num_colors)
        colors = [
            f'rgba({int(c[0]*255)}, {int(c[1]*255)}, {int(c[2]*255)}, 1.0)'
            for c in cmap(np.linspace(0, 1, num_colors))
        ]
    elif isinstance(color_def, list):
        # Assume it's a list of hex colors
        colors = [hex_to_rgba(color_def[i % len(color_def)]) for i in range(num_colors)]
    else:
        # Default to viridis colormap
        cmap = cm.get_cmap('viridis', num_colors)
        colors = [
            f'rgba({int(c[0]*255)}, {int(c[1]*255)}, {int(c[2]*255)}, 1.0)'
            for c in cmap(np.linspace(0, 1, num_colors))
        ]
    return colors

# Build group indices
group_indices = {}
for group_name, label_list in group_labels.items():
    indices = [original_label_to_index[label] for label in label_list]
    group_indices[group_name] = indices

# Assemble marker_colors array
marker_colors = [None] * len(labels)

for group_name, indices in group_indices.items():
    colors = get_group_colors(indices, group_name)
    for idx, color in zip(indices, colors):
        marker_colors[idx] = color

# Adjust text font color based on background color for readability
def get_text_color(rgba_color):
    rgba = [int(x) for x in re.findall(r'\d+', rgba_color)[:3]]  # Extract RGB values
    luminance = (0.299 * rgba[0] + 0.587 * rgba[1] + 0.114 * rgba[2]) / 255
    return 'black' if luminance > 0.5 else 'white'

text_colors = [get_text_color(c) for c in marker_colors]

# Create the treemap with branchvalues='total'
fig = go.Figure(go.Treemap(
    labels=labels,
    parents=parents,
    values=values_in_MB,
    marker=dict(colors=marker_colors),
    text=text,  # Use custom text for child nodes
    textfont=dict(color=text_colors, size=16, family='Helvetica'),
    textinfo='label+text',  # Display label and text
    branchvalues='total',
))

# Update layout for better readability and adjust uniform text settings
fig.update_layout(
    title="Detailed Memory Allocation of 'Truck' scene in 3D Gaussian Splatting, .ply format",
    margin=dict(t=50, l=25, r=25, b=25),
    uniformtext=dict(minsize=10, mode='hide')  # Hide text that doesn't fit
)

# Adjust the layout to set the figure size to a 16:9 aspect ratio
fig.update_layout(
    width=1920,
    height=1080
)

# Export the figure as a PDF and PNG file
fig.write_image("treemap_plot.pdf")
fig.write_image("treemap_plot.png")
