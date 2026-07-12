"""Generate a clean open-book dictionary icon (transparent bg)"""
from PIL import Image, ImageDraw

OUT = r"J:\code\MI band\腕上词典\src\common\deco-icon.png"
S = 200  # work at 2x for smooth edges

img = Image.new("RGBA", (S, S), (0, 0, 0, 0))
d = ImageDraw.Draw(img)

BLUE = (29, 116, 232, 255)
BLUE_DK = (17, 82, 178, 255)
WHITE = (255, 255, 255, 255)
PAPER = (240, 246, 255, 255)
GREY = (150, 170, 205, 255)

cx = S / 2

# ---- Book cover (slightly larger blue shape behind pages) ----
# Approximate open book cover as a rounded "valley" shape
cover = [
    (28, 52),
    (cx, 70),
    (S - 28, 52),
    (S - 30, 150),
    (cx, 168),
    (30, 150),
]
d.polygon(cover, fill=BLUE)

# cover side shading
d.polygon([(28, 52), (cx, 70), (cx, 168), (30, 150)], fill=BLUE_DK)

# ---- Left page ----
left_page = [
    (34, 60),
    (cx - 4, 76),
    (cx - 4, 158),
    (34, 142),
]
d.polygon(left_page, fill=PAPER)

# ---- Right page ----
right_page = [
    (S - 34, 60),
    (cx + 4, 76),
    (cx + 4, 158),
    (S - 34, 142),
]
d.polygon(right_page, fill=WHITE)

# ---- Spine highlight ----
d.line([(cx, 74), (cx, 160)], fill=BLUE, width=3)

# ---- Text lines on left page ----
for i, y in enumerate(range(86, 150, 12)):
    x0 = 42
    x1 = cx - 12
    # taper lines near spine
    d.line([(x0, y), (x1, y + 2)], fill=GREY, width=2)

# ---- Text lines on right page ----
for i, y in enumerate(range(86, 150, 12)):
    x0 = cx + 12
    x1 = S - 42
    d.line([(x0, y + 2), (x1, y)], fill=GREY, width=2)

# ---- Bookmark ribbon (accent) ----
d.polygon([(cx - 6, 70), (cx + 6, 70), (cx + 6, 120), (cx, 110), (cx - 6, 120)], fill=(255, 196, 0, 255))

# downscale with anti-aliasing
img = img.resize((100, 100), Image.LANCZOS)
img.save(OUT)
import os
print(f"Saved: {os.path.getsize(OUT)} bytes, size={img.size}")
