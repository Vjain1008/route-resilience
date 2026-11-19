"""
Generates multi-junction urban corridor tiles showing multiple consecutive intersections
with varying road sizes (Major Arterial, Secondary Collector, Local Street).
"""

import os
from PIL import Image, ImageDraw

def generate_multi_junction_corridor(output_path="data/sample_images/corridor_multi_junction.jpg"):
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    w, h = 800, 600
    img = Image.new("RGB", (w, h), color=(30, 41, 59))
    draw = ImageDraw.Draw(img)

    # 1. Main Arterial Corridor: East-West spine (6-Lane, Width 50px ~ 25m)
    # y from 275 to 325
    draw.rectangle([(0, 275), (w, 325)], fill=(71, 85, 105))
    # Dashed lane markings
    for x in range(0, w, 40):
        draw.line([(x, 300), (x + 20, 300)], fill=(255, 255, 255), width=2)

    # 2. Crossroad 1: North-South Major Arterial at x=200 (4-Lane, Width 40px ~ 20m)
    draw.rectangle([(180, 0), (220, h)], fill=(71, 85, 105))
    for y in range(0, h, 40):
        draw.line([(200, y), (200, y + 20)], fill=(255, 255, 255), width=2)

    # 3. Side Avenue 2: T-Junction North at x=400 (3-Lane, Width 30px ~ 15m, terminates at main road)
    draw.rectangle([(385, 0), (415, 300)], fill=(71, 85, 105))
    for y in range(0, 300, 40):
        draw.line([(400, y), (400, y + 20)], fill=(255, 255, 255), width=2)

    # 4. Crossroad 3: North-South Secondary Road at x=620 (4-Lane, Width 36px ~ 18m)
    draw.rectangle([(602, 0), (638, h)], fill=(71, 85, 105))
    for y in range(0, h, 40):
        draw.line([(620, y), (620, y + 20)], fill=(255, 255, 255), width=2)

    # Intersection boxes
    draw.rectangle([(180, 275), (220, 325)], fill=(100, 116, 139))
    draw.rectangle([(385, 275), (415, 325)], fill=(100, 116, 139))
    draw.rectangle([(602, 275), (638, 325)], fill=(100, 116, 139))

    # Buildings between roads
    bldg_col = (51, 65, 85)
    draw.rectangle([(40, 40), (140, 230)], fill=bldg_col, outline=(148, 163, 184), width=2)
    draw.rectangle([(260, 40), (340, 230)], fill=bldg_col, outline=(148, 163, 184), width=2)
    draw.rectangle([(460, 40), (560, 230)], fill=bldg_col, outline=(148, 163, 184), width=2)
    draw.rectangle([(680, 40), (760, 230)], fill=bldg_col, outline=(148, 163, 184), width=2)

    draw.rectangle([(40, 370), (140, 550)], fill=bldg_col, outline=(148, 163, 184), width=2)
    draw.rectangle([(260, 370), (560, 550)], fill=bldg_col, outline=(148, 163, 184), width=2)
    draw.rectangle([(680, 370), (760, 550)], fill=bldg_col, outline=(148, 163, 184), width=2)

    # Tree occlusions
    for tx, ty in [(180, 150), (415, 180), (602, 420), (300, 275), (520, 325)]:
        draw.ellipse([(tx - 20, ty - 20), (tx + 20, ty + 20)], fill=(22, 101, 52))

    draw.text((20, 20), "MULTI-JUNCTION CORRIDOR (J1: 4-Way, J2: T-Junction, J3: 4-Way)", fill=(248, 250, 252))
    img.save(output_path, quality=95)
    print(f"Generated multi-junction corridor image: {output_path}")

if __name__ == "__main__":
    generate_multi_junction_corridor()
