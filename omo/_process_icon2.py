"""Remove gray watermark text from bottom-right, keep white bg, resize"""
from PIL import Image

SRC = r"C:\Users\Administrator\Downloads\17cd6d44d02f4.png"
OUT = r"J:\code\MI band\腕上词典\src\common\deco-icon.png"

img = Image.open(SRC).convert("RGB")
w, h = img.size
pixels = img.load()

# Watermark area: bottom-right text in gray (~191) on white bg
# Strategy: identify gray text pixels and replace with white
# Text pixels are gray (brightness 150-230) surrounded by white (brightness > 240)
wm_removed = 0
for y in range(h - 90, h - 5):          # y: 934-1019
    for x in range(w - 200, w - 10):     # x: 824-1014
        r, g, b = pixels[x, y]
        bright = (r + g + b) / 3
        
        # Gray watermark text: brightness between 150-230, relatively uniform gray
        if 150 <= bright <= 235 and abs(r - g) < 12 and abs(g - b) < 12:
            # Check if surrounded by white (background)
            white_around = 0
            total_check = 0
            for dy in (-4, -2, 2, 4):
                for dx in (-4, -2, 2, 4):
                    nx, ny = x + dx, y + dy
                    if 0 <= nx < w and 0 <= ny < h:
                        nr, ng, nb = pixels[nx, ny]
                        if (nr + ng + nb) / 3 > 240:
                            white_around += 1
                        total_check += 1
            
            if total_check > 0 and white_around / total_check > 0.4:
                pixels[x, y] = (255, 255, 255)
                wm_removed += 1

print(f"Watermark pixels removed: {wm_removed}")

# Find subject center (brightness-weighted, excluding white bg)
total_w, sx, sy = 0, 0.0, 0.0
min_x, max_x = w, 0
min_y, max_y = h, 0
white_bg_count = 0

for y in range(h):
    for x in range(w):
        r, g, b = pixels[x, y]
        bright = (r + g + b) / 3
        is_white = bright > 235 and abs(r - g) < 10 and abs(g - b) < 10
        if is_white:
            white_bg_count += 1
        else:
            weight = max(255 - bright, 1)  # darker = heavier weight
            total_w += weight
            sx += x * weight
            sy += y * weight
            if x < min_x: min_x = x
            if x > max_x: max_x = x
            if y < min_y: min_y = y
            if y > max_y: max_y = y

print(f"White bg pixels: {white_bg_count}")
print(f"Subject bbox: ({min_x},{min_y}) to ({max_x},{max_y})")
cx = sx / total_w if total_w else w / 2
cy = sy / total_w if total_w else h / 2
print(f"Weighted center: ({cx:.1f}, {cy:.1f})")

# Crop with padding and make square
box_w = max_x - min_x
box_h = max_y - min_y
pad = 0.12
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
final = cropped.resize((100, 100), Image.LANCZOS)
final.save(OUT)
import os
print(f"Saved: {os.path.getsize(OUT)} bytes")
