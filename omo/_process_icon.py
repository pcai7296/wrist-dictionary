"""Process deco icon: remove watermark on white bg, resize"""
from PIL import Image

SRC = r"C:\Users\Administrator\Downloads\17cd6d44d02f4.png"
OUT = r"J:\code\MI band\腕上词典\src\common\deco-icon.png"

img = Image.open(SRC).convert("RGB")
w, h = img.size
pixels = img.load()

# Find watermark: white text on slightly darker bg in bottom-right
# Strategy: detect isolated bright pixels surrounded by darker ones
watermark_pixels = []
for y in range(h - 80, h):
    for x in range(w - 200, w - 10):
        r, g, b = pixels[x, y]
        bright = (r + g + b) / 3
        if bright > 200:
            # Check neighbors — if most are darker, this is text
            darker = 0
            total = 0
            for dy in (-3, -2, -1, 1, 2, 3):
                for dx in (-3, -2, -1, 1, 2, 3):
                    nx, ny = x + dx, y + dy
                    if 0 <= nx < w and 0 <= ny < h:
                        nr, ng, nb = pixels[nx, ny]
                        if (nr + ng + nb) / 3 < 180:
                            darker += 1
                        total += 1
            if total > 0 and darker / total > 0.25:
                watermark_pixels.append((x, y))

print(f"Watermark pixels detected: {len(watermark_pixels)}")

# Before inpainting, make a copy to sample from
img_copy = img.copy()
copy_pixels = img_copy.load()

# Inpaint watermark pixels with surrounding non-text color
for x, y in watermark_pixels:
    # Sample nearby non-watermark pixels
    samples = []
    for dy in range(-6, 7):
        for dx in range(-6, 7):
            if dx == 0 and dy == 0:
                continue
            nx, ny = x + dx, y + dy
            if 0 <= nx < w and 0 <= ny < h and (nx, ny) not in watermark_pixels:
                nr, ng, nb = copy_pixels[nx, ny]
                samples.append((nr, ng, nb))
    if samples:
        avg_r = sum(s[0] for s in samples) // len(samples)
        avg_g = sum(s[1] for s in samples) // len(samples)
        avg_b = sum(s[2] for s in samples) // len(samples)
        pixels[x, y] = (avg_r, avg_g, avg_b)

# Now the bg is already white/light.
# Find subject by looking for non-white pixels
min_x, max_x = w, 0
min_y, max_y = h, 0
total_w, sx, sy = 0, 0.0, 0.0
for y in range(h):
    for x in range(w):
        r, g, b = pixels[x, y]
        bright = (r + g + b) / 3
        # Subject: not white (bright < 240) or not near-white
        if bright < 230 or abs(r - g) + abs(g - b) > 20:
            total_w += 1
            sx += x
            sy += y
            if x < min_x: min_x = x
            if x > max_x: max_x = x
            if y < min_y: min_y = y
            if y > max_y: max_y = y

print(f"Subject bbox: ({min_x},{min_y}) to ({max_x},{max_y})")
cx = sx / total_w if total_w else w // 2
cy = sy / total_w if total_w else h // 2
print(f"Center: ({cx:.1f}, {cy:.1f})")

# Crop with padding
box_w = max_x - min_x
box_h = max_y - min_y
pad = 0.15
crop_size = max(box_w, box_h) * (1 + pad)
left = int(max(0, cx - crop_size / 2))
top = int(max(0, cy - crop_size / 2))
right = int(min(w, left + crop_size))
bottom = int(min(h, top + crop_size))
# Re-center if we hit edge
if right - left < crop_size * 0.85:
    left = max(0, right - int(crop_size))
if bottom - top < crop_size * 0.85:
    top = max(0, bottom - int(crop_size))
# Make square
size = min(right - left, bottom - top)
if size < 10:
    size = 100
cx2 = (left + right) / 2
cy2 = (top + bottom) / 2
left = int(cx2 - size / 2)
top = int(cy2 - size / 2)
right = left + size
bottom = top + size
# Clip to image bounds
left = max(0, left)
top = max(0, top)
right = min(w, right)
bottom = min(h, bottom)

print(f"Crop: ({left},{top}) to ({right},{bottom}) [{right-left}x{bottom-top}]")

cropped = img.crop((left, top, right, bottom))

# Resize to 100x100
final = cropped.resize((100, 100), Image.LANCZOS)
final.save(OUT)
import os
print(f"Saved: {os.path.getsize(OUT)} bytes")
