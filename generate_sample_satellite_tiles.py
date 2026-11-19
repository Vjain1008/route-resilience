"""
Generates realistic synthetic aerial/satellite junction tiles for trial evaluation.
Used by app.py and CLI demos.
"""

import os
from PIL import Image, ImageDraw

def generate_samples(output_dir="data/sample_images"):
    os.makedirs(output_dir, exist_ok=True)
    junctions = [
        ("silk_board.jpg", (30, 41, 59), "Central Silk Board (Bengaluru)"),
        ("ito_delhi.jpg", (40, 50, 60), "ITO Junction (New Delhi)"),
        ("chandani_chowk.jpg", (45, 55, 45), "Chandani Chowk (Pune)"),
        ("kathipara_chennai.jpg", (35, 45, 55), "Kathipara Junction (Chennai)")
    ]

    for fname, bg_color, name in junctions:
        img = Image.new("RGB", (600, 600), color=bg_color)
        draw = ImageDraw.Draw(img)

        # Draw road asphalt grid
        road_color = (71, 85, 105)
        # N-S corridor
        draw.rectangle([(275, 0), (325, 600)], fill=road_color)
        # E-W corridor
        draw.rectangle([(0, 275), (600, 325)], fill=road_color)
        # Intersection box
        draw.rectangle([(270, 270), (330, 330)], fill=(100, 116, 139))

        # Lane markings
        for y in range(0, 600, 40):
            draw.line([(300, y), (300, y + 20)], fill=(255, 255, 255), width=2)
        for x in range(0, 600, 40):
            draw.line([(x, 300), (x + 20, 300)], fill=(255, 255, 255), width=2)

        # Draw building blocks
        draw.rectangle([(60, 60), (220, 220)], fill=(51, 65, 85), outline=(148, 163, 184), width=2)
        draw.rectangle([(380, 60), (540, 220)], fill=(51, 65, 85), outline=(148, 163, 184), width=2)
        draw.rectangle([(60, 380), (220, 540)], fill=(51, 65, 85), outline=(148, 163, 184), width=2)
        draw.rectangle([(380, 380), (540, 540)], fill=(51, 65, 85), outline=(148, 163, 184), width=2)

        # Draw tree canopy occlusions along road edges (green blobs with Excess Green Index)
        tree_green = (22, 101, 52)
        for tx, ty in [(250, 150), (250, 420), (350, 180), (450, 250), (150, 350)]:
            draw.ellipse([(tx - 25, ty - 25), (tx + 25, ty + 25)], fill=tree_green)

        # Draw building shadows (dark patches)
        shadow_color = (15, 23, 42)
        draw.polygon([(220, 220), (250, 250), (250, 220)], fill=shadow_color)
        draw.polygon([(380, 220), (410, 250), (410, 220)], fill=shadow_color)

        # Label tile
        draw.text((20, 20), f"AERIAL SAT TILE: {name}", fill=(248, 250, 252))

        out_path = os.path.join(output_dir, fname)
        img.save(out_path, quality=92)
        print(f"Generated sample tile: {out_path}")

if __name__ == "__main__":
    generate_samples()
