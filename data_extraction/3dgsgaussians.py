import os
import pandas as pd
from pyntcloud import PyntCloud #pip install pyntcloud

# Define the dataset and scenes
dataset_scenes = {
    'DeepBlending': ["drjohnson", "playroom"], 
    'SyntheticNeRF': ["drums", "ficus", "hotdog", "lego", "materials", "mic", "ship", "chair"], 
    'TanksAndTemples': ["train", "truck"], 
    'MipNeRF360': ["garden", "bicycle", "stump", "bonsai", "counter", "kitchen", "room", "treehill", "flowers"]
}

main_dir = 'C:/Users/knoll/Desktop/3dgsgaussians'

# Initialize a dictionary to store total points and counts per dataset
dataset_points = {dataset: {"total_points": 0, "scene_count": 0} for dataset in dataset_scenes}

# Traverse each dataset and its scenes
for dataset, scenes in dataset_scenes.items():
    for scene in scenes:
        scene_dir = os.path.join(main_dir, scene, 'point_cloud', 'iteration_30000')

        # Check if the point_cloud.ply file exists in the expected directory
        ply_file_path = os.path.join(scene_dir, 'point_cloud.ply')
        if os.path.isfile(ply_file_path):
            # Read the point cloud file
            cloud = PyntCloud.from_file(ply_file_path)
            num_points = len(cloud.points)
            
            # Update the dataset points and scene count
            dataset_points[dataset]["total_points"] += num_points
            dataset_points[dataset]["scene_count"] += 1

            # Print the scene name and the number of points
            print(f"Folder: {scene}, Points: {num_points}")
        else:
            print(f"point_cloud.ply not found in {scene}")

# Calculate and print the average points per dataset
print("\nAverage Points per Dataset:")
for dataset, data in dataset_points.items():
    if data["scene_count"] > 0:
        average_points = data["total_points"] / data["scene_count"]
        print(f"{dataset}: {average_points:.2f} points (average across {data['scene_count']} scenes)")
    else:
        print(f"{dataset}: No valid point clouds found.")

print("done")