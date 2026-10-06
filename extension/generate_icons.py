"""One-off script to generate the extension's PNG icon set. Run once with
Pillow available (e.g. `docker compose exec backend python /path/to/this`),
not part of the extension's runtime or build.
"""

import math

from PIL import Image, ImageDraw

NAVY_950 = (5, 7, 13, 255)
BRAND_BLUE = (59, 130, 246, 255)
BRAND_CYAN = (34, 211, 238, 255)

SIZES = (16, 32, 48, 128)


def _gradient_rounded_square(size: int) -> Image.Image:
    img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    gradient = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    for y in range(size):
        for x in range(size):
            t = (x + y) / (2 * size)
            r = int(BRAND_BLUE[0] + (BRAND_CYAN[0] - BRAND_BLUE[0]) * t)
            g = int(BRAND_BLUE[1] + (BRAND_CYAN[1] - BRAND_BLUE[1]) * t)
            b = int(BRAND_BLUE[2] + (BRAND_CYAN[2] - BRAND_BLUE[2]) * t)
            gradient.putpixel((x, y), (r, g, b, 255))

    mask = Image.new("L", (size, size), 0)
    mask_draw = ImageDraw.Draw(mask)
    radius = max(2, size // 5)
    mask_draw.rounded_rectangle([0, 0, size - 1, size - 1], radius=radius, fill=255)
    img.paste(gradient, (0, 0), mask)
    return img


def _shield_path(size: int) -> list[tuple[float, float]]:
    cx = size / 2
    top = size * 0.16
    bottom = size * 0.88
    left = size * 0.22
    right = size * 0.78
    mid = size * 0.55
    return [
        (cx, top),
        (right, size * 0.28),
        (right, mid),
        (cx, bottom),
        (left, mid),
        (left, size * 0.28),
    ]


def _draw_shield_and_check(img: Image.Image, size: int) -> None:
    draw = ImageDraw.Draw(img)
    draw.polygon(_shield_path(size), fill=NAVY_950)

    # checkmark, drawn as a thick line
    check_width = max(1, round(size * 0.09))
    p1 = (size * 0.35, size * 0.5)
    p2 = (size * 0.46, size * 0.62)
    p3 = (size * 0.67, size * 0.36)
    draw.line([p1, p2], fill=BRAND_CYAN, width=check_width, joint="curve")
    draw.line([p2, p3], fill=BRAND_CYAN, width=check_width, joint="curve")
    r = check_width / 2
    for p in (p1, p2, p3):
        draw.ellipse([p[0] - r, p[1] - r, p[0] + r, p[1] + r], fill=BRAND_CYAN)


def make_icon(size: int) -> Image.Image:
    img = _gradient_rounded_square(size)
    _draw_shield_and_check(img, size)
    return img


if __name__ == "__main__":
    import os

    out_dir = os.path.join(os.path.dirname(__file__), "icons")
    os.makedirs(out_dir, exist_ok=True)
    for size in SIZES:
        icon = make_icon(size)
        icon.save(os.path.join(out_dir, f"icon{size}.png"))
        print(f"wrote icon{size}.png")
