from PIL import Image
import os

# Define the folder path
folder_path = "project-page/static/images"

# Target display height
display_height = 250

# Multiplier for high-resolution images (e.g., 2 for Retina displays)
multiplier = 2

# High-resolution height
high_res_height = display_height * multiplier

# Process each image in the folder
for filename in os.listdir(folder_path):
    if filename.lower().endswith((".png", ".jpg", ".jpeg")):
        if "_h250" in filename or "_h500" in filename:
            continue

        file_path = os.path.join(folder_path, filename)

        # Open the image
        img = Image.open(file_path)
        # Get the original size
        original_width, original_height = img.size

        # Resize to 250px height (1x)
        new_width_1x = int((display_height / original_height) * original_width)
        img_1x = img.resize((new_width_1x, display_height), Image.LANCZOS)

        # Save the 1x version as WebP with height in the filename
        base, _ = os.path.splitext(filename)
        img_1x.save(
            os.path.join(folder_path, f"{base}_h{display_height}px.webp"),
            format="webp",
            quality=80,
        )
        print(
            f"Resized and saved {base}_{display_height}px.webp to {new_width_1x}x{display_height}"
        )

        # Resize to 500px height (2x for high-DPI displays)
        new_width_2x = int((high_res_height / original_height) * original_width)
        img_2x = img.resize((new_width_2x, high_res_height), Image.LANCZOS)

        # Save the 2x version as WebP with height in the filename
        img_2x.save(
            os.path.join(folder_path, f"{base}_h{high_res_height}px.webp"),
            format="webp",
            quality=80,
        )
        print(
            f"Resized and saved {base}_{high_res_height}px@2x.webp to {new_width_2x}x{high_res_height}"
        )

        # Save the original image as a PDF
        pdf_path = os.path.join(folder_path, f"{base}.pdf")
        img.save(pdf_path, "PDF", resolution=100.0)
        print(f"Saved {base}.pdf at full resolution")
print("Processing complete!")
