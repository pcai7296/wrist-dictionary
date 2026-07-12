"""Convert white bg to black and white lines to black"""
from PIL import Image

SRC = r"C:\Users\Administrator\Downloads\17cd6d44d02f4.png"
OUT = r"J:\code\MI band\腕上词典\src\common\deco-icon.png"

img = Image.open(SRC).convert("RGB")
w, h = img.size
pixels = img.load()

# Threshold: anything brighter than this becomes black
# Book core is brightness 0-19, so threshold at ~30 keeps book + kills bg + edges
THRESHOLD = 30

changed = 0
kept = 0
for y in range(h):
    for x in range(w):
        r, g, b = pixels[x, y]
        bright = (r + g + b) / 3
        if bright > THRESHOLD:
            pixels[x, y] = (0, 0, 0)  # black
            changed += 1
        else:
            kept += 1

print(f"Pixels changed to black: {changed} ({changed/w/h*100:.1f}%)")
print(f"Pixels kept (book core): {kept} ({kept/w/h*100:.1f}%)")

# Find center of kept pixels
total_w, sx, sy = 0, 0.0, 0.0
min_x, max_x = w, 0
min_y, max_y = h, 0
for y in range(h):
    for x in range(w):
        r, g, b = pixels[x, y]
        if (r + g + b) > 0:  # non-black (kept book pixel)
            weight = 256 - (r + g + b) / 3
            total_w += weight
            sx += x * weight
            sy += y * weight
            if x < min_x: min_x = x
            if x > max_x: max_x = x
            if y < min_y: min_y = y
            if y > max_y: max_y = y

cx = sx / total_w if total_w else w // 2
cy = sy / total_w if total_w else h // 2
print(f"Book center: ({cx:.1f}, {cy:.1f})")
print(f"Book bbox: ({min_x},{min_y}) to ({max_x},{max_y})")

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
left = int(max(0, (left + right) / 2 - sz / 2))
top = int(max(0, (top + bottom) / 2 - sz / 2))
right = int(min(w, left + sz))
bottom = int(min(h, top + sz))
print(f"Crop: ({left},{top}) to ({right},{bottom})")

cropped = img.crop((left, top, right, bottom))
final = cropped.resize((100, 100), Image.LANCZOS)
final.save(OUT)
import os
print(f"Saved: {os.path.getsize(OUT)} bytes")
