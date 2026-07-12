"""Remove watermark from dict icon, resize to 100x100"""
from PIL import Image, ImageFilter
import collections

SRC = r"C:\Users\Administrator\Downloads\e8ab3592a7f1d8.png"
OUT = r"J:\code\MI band\腕上词典\src\common\deco-icon.png"

img = Image.open(SRC).convert("RGB")
w, h = img.size
pixels = img.load()

# Watermark locations identified:
# 1. Bottom-right: rows 946-992, x=917-996, gray text ~RGB(130-164)
# 2. Top-right: rows 80-109, x=898-990, gray text ~RGB(130-164)
# Watermark pixels: uniform gray (RGB close), brightness 60-200, on dark background

def is_watermark(x, y, r, g, b):
    """Check if pixel is likely watermark text on dark background."""
    bright = (r + g + b) / 3
    if not (60 <= bright <= 210 and abs(r - g) < 20 and abs(g - b) < 20):
        return False
    # Check location
    in_bottom = y > 918 and x > 910
    in_top = 75 <= y <= 115 and x > 890
    if not (in_bottom or in_top):
        return False
    # Must have at least 2 dark neighbors (background is dark)
    dark_count = 0
    for dx, dy in [(-1,0),(1,0),(0,-1),(0,1),(-1,-1),(-1,1),(1,-1),(1,1)]:
        nx, ny = x + dx, y + dy
        if 0 <= nx < w and 0 <= ny < h:
            nr, ng, nb = pixels[nx, ny]
            if (nr + ng + nb) / 3 < 35:
                dark_count += 1
    return dark_count >= 2

removed = 0
for y in range(h):
    for x in range(w):
        r, g, b = pixels[x, y]
        if is_watermark(x, y, r, g, b):
            pixels[x, y] = (0, 0, 0)  # replace with black bg
            removed += 1

print(f"Watermark pixels removed: {removed}")

# Find subject center (brightness-weighted, excluding near-black and isolated gray)
total_w, sx, sy = 0, 0.0, 0.0
min_x, max_x = w, 0
min_y, max_y = h, 0
subject_pixels = 0

for y in range(h):
    for x in range(w):
        r, g, b = pixels[x, y]
        bright = (r + g + b) / 3
        if bright > 20:  # ignore near-black
            weight = min(bright, 255)
            total_w += weight
            sx += x * weight
            sy += y * weight
            subject_pixels += 1
            if x < min_x: min_x = x
            if x > max_x: max_x = x
            if y < min_y: min_y = y
            if y > max_y: max_y = y

cx = sx / total_w if total_w else w // 2
cy = sy / total_w if total_w else h // 2
print(f"Subject pixels: {subject_pixels}")
print(f"Weighted center: ({cx:.1f}, {cy:.1f})")
print(f"Subject bbox: ({min_x},{min_y}) to ({max_x},{max_y}) [{max_x-min_x}x{max_y-min_y}]")

# Crop with padding
box_w = max_x - min_x
box_h = max_y - min_y
pad = 0.15
size = max(box_w, box_h) * (1 + pad)
left = int(max(0, cx - size / 2))
top = int(max(0, cy - size / 2))
right = int(min(w, left + size))
bottom = int(min(h, top + size))

# Make square
sz = min(right - left, bottom - top)
cx2 = (left + right) / 2
cy2 = (top + bottom) / 2
left = int(max(0, cx2 - sz / 2))
top = int(max(0, cy2 - sz / 2))
right = int(min(w, left + sz))
bottom = int(min(h, top + sz))

print(f"Crop: ({left},{top}) to ({right},{bottom}) [{right-left}x{bottom-top}]")

cropped = img.crop((left, top, right, bottom))
# Apply slight sharpen to preserve detail after resize
cropped = cropped.filter(ImageFilter.SHARPEN)
final = cropped.resize((100, 100), Image.LANCZOS)
final.save(OUT)
import os
print(f"Saved: {os.path.getsize(OUT)} bytes")
