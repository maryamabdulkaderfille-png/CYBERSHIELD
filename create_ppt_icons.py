import os
from PIL import Image, ImageDraw

def create_icons(output_dir="ppt_assets"):
    os.makedirs(output_dir, exist_ok=True)
    size = 128
    
    # Exact CyberShield System Brand Colors
    NAVY = (10, 14, 26, 255)        # #0A0E1A (CyberShield Navy-900)
    BRAND_BLUE = (59, 130, 246, 255) # #3B82F6 (CyberShield Brand Blue)
    BRAND_CYAN = (34, 211, 238, 255) # #22D3EE (CyberShield Brand Cyan)
    WHITE = (255, 255, 255, 255)
    SAFE_GREEN = (34, 197, 94, 255)  # #22C55E (CyberShield Safe)
    DANGER_RED = (239, 68, 68, 255)  # #EF4444 (CyberShield Danger)
    
    def base_circle(bg_color):
        img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
        draw = ImageDraw.Draw(img)
        draw.ellipse([4, 4, size - 5, size - 5], fill=bg_color)
        return img, draw

    # 1. Shield Icon (CyberShield Logo replica)
    img, draw = base_circle(NAVY)
    points = [
        (64, 24),
        (96, 36),
        (96, 68),
        (64, 104),
        (32, 68),
        (32, 36)
    ]
    draw.polygon(points, fill=BRAND_BLUE)
    # Checkmark inside shield with Cyan
    draw.line([(48, 64), (58, 76), (82, 48)], fill=BRAND_CYAN, width=8)
    img.save(f"{output_dir}/shield.png")

    # 2. Alert / Warning Icon
    img, draw = base_circle(DANGER_RED)
    tri = [(64, 26), (102, 98), (26, 98)]
    draw.polygon(tri, fill=WHITE)
    draw.line([(64, 48), (64, 74)], fill=NAVY, width=8)
    draw.ellipse([60, 82, 68, 90], fill=NAVY)
    img.save(f"{output_dir}/alert.png")

    # 3. Target / Bullseye (Objectives)
    img, draw = base_circle(NAVY)
    draw.ellipse([24, 24, 104, 104], outline=WHITE, width=6)
    draw.ellipse([42, 42, 86, 86], outline=BRAND_CYAN, width=6)
    draw.ellipse([56, 56, 72, 72], fill=BRAND_BLUE)
    img.save(f"{output_dir}/target.png")

    # 4. Book (Literature Review)
    img, draw = base_circle(NAVY)
    draw.rounded_rectangle([28, 38, 60, 92], radius=4, fill=WHITE)
    draw.rounded_rectangle([68, 38, 100, 92], radius=4, fill=WHITE)
    draw.line([(34, 48), (54, 48)], fill=BRAND_CYAN, width=3)
    draw.line([(34, 58), (54, 58)], fill=BRAND_BLUE, width=3)
    draw.line([(34, 68), (54, 68)], fill=BRAND_BLUE, width=3)
    draw.line([(74, 48), (94, 48)], fill=BRAND_CYAN, width=3)
    draw.line([(74, 58), (94, 58)], fill=BRAND_BLUE, width=3)
    draw.line([(74, 68), (94, 68)], fill=BRAND_BLUE, width=3)
    img.save(f"{output_dir}/book.png")

    # 5. Gears / Methodology
    img, draw = base_circle(NAVY)
    draw.ellipse([34, 34, 94, 94], outline=BRAND_CYAN, width=12)
    draw.ellipse([50, 50, 78, 78], fill=WHITE)
    draw.ellipse([58, 58, 70, 70], fill=BRAND_BLUE)
    for ang in [0, 45, 90, 135]:
        draw.line([(64, 20), (64, 34)], fill=BRAND_CYAN, width=8)
        draw.line([(64, 94), (64, 108)], fill=BRAND_CYAN, width=8)
        draw.line([(20, 64), (34, 64)], fill=BRAND_CYAN, width=8)
        draw.line([(94, 64), (108, 64)], fill=BRAND_CYAN, width=8)
    img.save(f"{output_dir}/method.png")

    # 6. Layers / System Design
    img, draw = base_circle(NAVY)
    for y, col in [(32, BRAND_CYAN), (54, WHITE), (76, BRAND_BLUE)]:
        pts = [(64, y), (100, y + 14), (64, y + 28), (28, y + 14)]
        draw.polygon(pts, fill=col)
    img.save(f"{output_dir}/layers.png")

    # 7. Code (Implementation)
    img, draw = base_circle(NAVY)
    draw.line([(46, 42), (32, 64), (46, 86)], fill=BRAND_CYAN, width=6)
    draw.line([(82, 42), (96, 64), (82, 86)], fill=BRAND_CYAN, width=6)
    draw.line([(70, 40), (58, 88)], fill=WHITE, width=5)
    img.save(f"{output_dir}/code.png")

    # 8. Test / Results (Safe Green Shield Check)
    img, draw = base_circle(SAFE_GREEN)
    draw.ellipse([20, 20, 108, 108], outline=WHITE, width=4)
    draw.line([(42, 64), (56, 80), (88, 48)], fill=WHITE, width=9)
    img.save(f"{output_dir}/test.png")

    # 9. Discussion (Chat Bubbles in CyberShield Blue/Cyan)
    img, draw = base_circle(NAVY)
    draw.rounded_rectangle([28, 32, 84, 72], radius=10, fill=WHITE)
    draw.polygon([(40, 72), (34, 86), (54, 72)], fill=WHITE)
    draw.rounded_rectangle([52, 54, 102, 90], radius=8, fill=BRAND_CYAN)
    draw.polygon([(92, 90), (98, 100), (80, 90)], fill=BRAND_CYAN)
    img.save(f"{output_dir}/discuss.png")

    # 10. Conclusion / Recommendations (Cap & Star)
    img, draw = base_circle(NAVY)
    pts = [(64, 38), (104, 54), (64, 70), (24, 54)]
    draw.polygon(pts, fill=BRAND_BLUE)
    draw.rectangle([46, 66, 82, 84], fill=WHITE)
    draw.line([(100, 54), (100, 86)], fill=BRAND_CYAN, width=4)
    draw.ellipse([96, 86, 104, 94], fill=BRAND_CYAN)
    img.save(f"{output_dir}/grad.png")

    # 11. University Logo / Crest
    img, draw = base_circle(NAVY)
    draw.ellipse([18, 18, 110, 110], outline=BRAND_CYAN, width=5)
    draw.polygon([(64, 30), (96, 44), (96, 76), (64, 100), (32, 76), (32, 44)], fill=WHITE)
    draw.line([(46, 62), (58, 74), (82, 50)], fill=BRAND_BLUE, width=6)
    img.save(f"{output_dir}/university.png")

    print("Icons regenerated with exact CyberShield brand colors!")

if __name__ == "__main__":
    create_icons()
