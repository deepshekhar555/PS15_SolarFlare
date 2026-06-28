import os
import numpy as np
from PIL import Image

def crop_sun_circles(image_path, num_cols=3, num_rows=2):
    img = Image.open(image_path).convert('RGB')
    w, h = img.size
    data = np.array(img)
    
    # Grid cell dimensions
    cell_w = w // num_cols
    cell_h = h // num_rows
    
    crops = []
    for r in range(num_rows):
        for c in range(num_cols):
            # Define cell bounding box
            x0 = c * cell_w
            y0 = r * cell_h
            x1 = (c + 1) * cell_w
            y1 = (r + 1) * cell_h
            
            cell_data = data[y0:y1, x0:x1]
            
            # Crop center 80% to avoid grid lines and white borders
            margin_w = int(cell_w * 0.1)
            margin_h = int(cell_h * 0.1)
            sub_cell = cell_data[margin_h:-margin_h, margin_w:-margin_w]
            
            # Find coordinates of non-black pixels in sub_cell
            gray = np.mean(sub_cell, axis=2)
            # Threshold to find the sun disk (avoiding the black background and white text/borders)
            mask = (gray > 15) & (gray < 245)
            
            y_indices, x_indices = np.where(mask)
            if len(x_indices) > 0 and len(y_indices) > 0:
                # Bounding box of the sun disk in sub_cell coordinates
                min_x, max_x = np.min(x_indices), np.max(x_indices)
                min_y, max_y = np.min(y_indices), np.max(y_indices)
                
                # Center and radius
                cx = (min_x + max_x) // 2 + margin_w
                cy = (min_y + max_y) // 2 + margin_h
                radius = max((max_x - min_x) // 2, (max_y - min_y) // 2)
                
                # Add a small padding
                pad = int(radius * 0.03)
                radius += pad
                
                # Crop a square around the sun disk in original image coordinates
                crop_x0 = x0 + cx - radius
                crop_y0 = y0 + cy - radius
                crop_x1 = x0 + cx + radius
                crop_y1 = y0 + cy + radius
                
                # Clip to image boundaries
                crop_x0 = max(0, crop_x0)
                crop_y0 = max(0, crop_y0)
                crop_x1 = min(w, crop_x1)
                crop_y1 = min(h, crop_y1)
                
                # Ensure it's a square
                side = min(crop_x1 - crop_x0, crop_y1 - crop_y0)
                crop_x1 = crop_x0 + side
                crop_y1 = crop_y0 + side
                
                cropped_img = img.crop((crop_x0, crop_y0, crop_x1, crop_y1))
                crops.append(cropped_img)
            else:
                # Fallback to center crop
                cx = cell_w // 2
                cy = cell_h // 2
                radius = min(cell_w, cell_h) // 3
                cropped_img = img.crop((x0 + cx - radius, y0 + cy - radius, x0 + cx + radius, y0 + cy + radius))
                crops.append(cropped_img)
    return crops

# Define paths
artifacts_dir = r"C:\Users\Welcome\.gemini\antigravity-ide\brain\9e2c343a-18e1-4f1e-a5de-6e3c5f218cd7"
img1_path = os.path.join(artifacts_dir, "media__1782613678714.png")
img2_path = os.path.join(artifacts_dir, "media__1782613705544.png")

output_dir = r"d:\PS15_SolarFlare"

print("Cropping Image 1...")
crops1 = crop_sun_circles(img1_path)
names1 = [
    "suit_396.png",            # Row 0, Col 0 (Call h 396.8 nm)
    "suit_388.png",            # Row 0, Col 1 (NB7 388 nm)
    "suit_300.png",            # Row 0, Col 2 (NB6 300 nm)
    "suit_purple_smooth.png",  # Row 1, Col 0
    "suit_green_textured.png", # Row 1, Col 1
    "suit_yellow_labeled.png"  # Row 1, Col 2
]
for i, crop in enumerate(crops1):
    crop.resize((512, 512), Image.Resampling.LANCZOS).save(os.path.join(output_dir, names1[i]))
    print(f"Saved {names1[i]}")

print("Cropping Image 2...")
crops2 = crop_sun_circles(img2_path)
names2 = [
    "suit_279.png",              # Row 0, Col 0 (Mg II k 279 nm)
    "suit_214.png",              # Row 0, Col 1 (NB1 214 nm)
    "suit_276.png",              # Row 0, Col 2 (NB2 276 nm)
    "suit_red_smooth.png",       # Row 1, Col 0
    "suit_violet_textured.png",  # Row 1, Col 1
    "suit_red_white_textured.png" # Row 1, Col 2
]
for i, crop in enumerate(crops2):
    crop.resize((512, 512), Image.Resampling.LANCZOS).save(os.path.join(output_dir, names2[i]))
    print(f"Saved {names2[i]}")

print("All SUIT images cropped and saved successfully.")
