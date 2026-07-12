"""Generate 10 distinct dictionary-icon styles into src/common/icons/"""
import os
from PIL import Image, ImageDraw, ImageFont

OUTDIR = r"J:\code\MI band\腕上词典\src\common\icons"
S = 200  # work 2x, downscale to 100
os.makedirs(OUTDIR, exist_ok=True)

FONT_DIR = "C:/Windows/Fonts"
f_arial_b = ImageFont.truetype(f"{FONT_DIR}/arialbd.ttf", 90)
f_arial_s = ImageFont.truetype(f"{FONT_DIR}/arialbd.ttf", 46)
f_simhei = ImageFont.truetype(f"{FONT_DIR}/simhei.ttf", 110)

BLUE = (29, 116, 232, 255)
BLUE_DK = (17, 82, 178, 255)
BLUE_LT = (90, 160, 245, 255)
WHITE = (255, 255, 255, 255)
PAPER = (235, 243, 255, 255)
GREY = (150, 170, 205, 255)
GOLD = (255, 196, 0, 255)
DARK = (20, 30, 50, 255)


def new():
    return Image.new("RGBA", (S, S), (0, 0, 0, 0))


def save(img, name):
    img = img.resize((100, 100), Image.LANCZOS)
    path = os.path.join(OUTDIR, name)
    img.save(path)
    print(f"  {name}: {os.path.getsize(path)} bytes")


# ---------- 01 flat open book ----------
def icon01():
    img = new()
    d = ImageDraw.Draw(img)
    cx = S / 2
    d.polygon([(28, 52), (cx, 70), (S - 28, 52), (S - 30, 150), (cx, 168), (30, 150)], fill=BLUE)
    d.polygon([(28, 52), (cx, 70), (cx, 168), (30, 150)], fill=BLUE_DK)
    d.polygon([(34, 60), (cx - 4, 76), (cx - 4, 158), (34, 142)], fill=PAPER)
    d.polygon([(S - 34, 60), (cx + 4, 76), (cx + 4, 158), (S - 34, 142)], fill=WHITE)
    d.line([(cx, 74), (cx, 160)], fill=BLUE, width=3)
    for y in range(86, 150, 12):
        d.line([(42, y), (cx - 12, y + 2)], fill=GREY, width=2)
        d.line([(cx + 12, y + 2), (S - 42, y)], fill=GREY, width=2)
    d.polygon([(cx - 6, 70), (cx + 6, 70), (cx + 6, 122), (cx, 112), (cx - 6, 122)], fill=GOLD)
    return img


# ---------- 02 glossy closed book (front) ----------
def icon02():
    img = new()
    d = ImageDraw.Draw(img)
    x0, y0, x1, y1 = 45, 35, 165, 165
    d.rounded_rectangle([x0, y0, x1, y1], radius=14, fill=BLUE)
    # vertical gradient sheen
    for i in range(int(y0), int(y1)):
        t = (i - y0) / (y1 - y0)
        shade = int(255 * (0.10 + 0.18 * (1 - t)))
        d.line([(x0 + 6, i), (x1 - 6, i)], fill=(255, 255, 255, shade), width=1)
    # glossy highlight
    d.ellipse([x0 + 14, y0 + 10, x0 + 70, y0 + 60], fill=(255, 255, 255, 70))
    # pages on right edge
    d.rectangle([x1 - 10, y0 + 14, x1 - 4, y1 - 14], fill=WHITE)
    for yy in range(y0 + 18, y1 - 14, 8):
        d.line([(x1 - 10, yy), (x1 - 4, yy)], fill=GREY, width=1)
    # spine line
    d.line([(x0 + 16, y0 + 6), (x0 + 16, y1 - 6)], fill=BLUE_DK, width=5)
    # bookmark
    d.polygon([(cx0 := 120, y0 + 6), (cx0 + 18, y0 + 6), (cx0 + 18, y0 + 70), (cx0 + 9, y0 + 58), (cx0, y0 + 70)], fill=GOLD)
    return img


# ---------- 03 book + magnifier ----------
def icon03():
    img = new()
    d = ImageDraw.Draw(img)
    cx = S / 2
    # open book (lower)
    d.polygon([(24, 120), (cx, 138), (S - 24, 120), (S - 26, 184), (cx, 200), (26, 184)], fill=BLUE)
    d.polygon([(30, 128), (cx - 4, 142), (cx - 4, 192), (30, 178)], fill=WHITE)
    d.polygon([(S - 30, 128), (cx + 4, 142), (cx + 4, 192), (S - 30, 178)], fill=PAPER)
    d.line([(cx, 140), (cx, 194)], fill=BLUE_DK, width=3)
    # magnifier (upper-right)
    mx, my, r = 140, 80, 42
    d.ellipse([mx - r, my - r, mx + r, my + r], outline=BLUE, width=12)
    d.ellipse([mx - r + 8, my - r + 8, mx + r - 8, my + r - 8], fill=(220, 235, 255, 255))
    d.line([(mx + r - 6, my + r - 6), (mx + r + 26, my + r + 26)], fill=BLUE_DK, width=14)
    # small A inside lens
    d.text((mx - 22, my - 30), "A", font=f_arial_b, fill=BLUE)
    return img


# ---------- 04 closed book vertical + ribbon ----------
def icon04():
    img = new()
    d = ImageDraw.Draw(img)
    x0, y0, x1, y1 = 55, 40, 150, 170
    d.rounded_rectangle([x0, y0, x1, y1], radius=10, fill=BLUE)
    d.rounded_rectangle([x0, y0, x1, y1], radius=10, outline=BLUE_DK, width=3)
    # pages right edge
    for i, off in enumerate(range(6, 22, 6)):
        d.line([(x1 - off, y0 + 6), (x1 - off, y1 - 6)], fill=WHITE, width=3)
    d.line([(x0 + 12, y0 + 8), (x0 + 12, y1 - 8)], fill=BLUE_DK, width=5)
    # title bar
    d.rounded_rectangle([x0 + 24, y0 + 26, x1 - 24, y0 + 44], radius=5, fill=WHITE)
    # ribbon
    d.polygon([(100, y0 + 4), (118, y0 + 4), (118, y0 + 70), (109, y0 + 58), (100, y0 + 70)], fill=GOLD)
    return img


# ---------- 05 Aa typography ----------
def icon05():
    img = new()
    d = ImageDraw.Draw(img)
    d.rounded_rectangle([28, 28, S - 28, S - 28], radius=26, fill=BLUE)
    d.rounded_rectangle([28, 28, S - 28, S - 28], radius=26, outline=BLUE_LT, width=4)
    d.text((40, 36), "Aa", font=f_arial_b, fill=WHITE)
    return img


# ---------- 06 stacked books ----------
def icon06():
    img = new()
    d = ImageDraw.Draw(img)
    books = [(40, 55, 160, 85, BLUE), (40, 90, 160, 120, BLUE_DK), (40, 125, 160, 155, BLUE_LT)]
    for (x0, y0, x1, y1, col) in books:
        d.rounded_rectangle([x0, y0, x1, y1], radius=8, fill=col)
        for yy in range(y0 + 6, y1 - 4, 7):
            d.line([(x0 + 10, yy), (x1 - 10, yy)], fill=(255, 255, 255, 120), width=2)
    # bookmark on top book
    d.polygon([(120, 50), (138, 50), (138, 92), (129, 82), (120, 92)], fill=GOLD)
    return img


# ---------- 07 line-art open book ----------
def icon07():
    img = new()
    d = ImageDraw.Draw(img)
    cx = S / 2
    # outlines only
    d.line([(30, 60), (cx, 82), (S - 30, 60)], fill=BLUE, width=5)
    d.line([(30, 60), (30, 140), (cx, 162), (cx, 82)], fill=BLUE, width=5)
    d.line([(S - 30, 60), (S - 30, 140), (cx, 162), (cx, 82)], fill=BLUE, width=5)
    d.line([(cx, 82), (cx, 162)], fill=BLUE, width=5)
    for y in range(96, 150, 14):
        d.line([(42, y), (cx - 14, y + 3)], fill=BLUE_LT, width=3)
        d.line([(cx + 14, y + 3), (S - 42, y)], fill=BLUE_LT, width=3)
    return img


# ---------- 08 pixel book ----------
def icon08():
    img = new()
    d = ImageDraw.Draw(img)
    grid = [
        "..bbbbbbbb..",
        ".bBBBBBBBBb.",
        "bBBwwwwwwBBb",
        "bBBwBBBBwBBb",
        "bBBwBBBBwBBb",
        "bBBwwwwwwBBb",
        "bBBwBBBBwBBb",
        "bBBwBBBBwBBb",
        "bBBwwwwwwBBb",
        "bBBBBBBBBBBb",
        ".bBBBBBBBBb.",
        "..bbbbbbbb..",
    ]
    cols = 12
    rows = len(grid)
    cell = int(S * 0.78 / cols)
    ox = (S - cols * cell) // 2
    oy = (S - rows * cell) // 2
    cmap = {"b": BLUE_DK, "B": BLUE, "w": WHITE}
    for r, row in enumerate(grid):
        for c, ch in enumerate(row):
            if ch != ".":
                d.rectangle([ox + c * cell, oy + r * cell, ox + (c + 1) * cell - 1, oy + (r + 1) * cell - 1], fill=cmap[ch])
    return img


# ---------- 09 dict block with 词 ----------
def icon09():
    img = new()
    d = ImageDraw.Draw(img)
    d.rounded_rectangle([26, 26, S - 26, S - 26], radius=28, fill=BLUE)
    d.rounded_rectangle([26, 26, S - 26, S - 26], radius=28, outline=BLUE_DK, width=5)
    # inner page panel
    d.rounded_rectangle([48, 48, S - 48, S - 48], radius=16, fill=(255, 255, 255, 230))
    d.text((50, 40), "词", font=f_simhei, fill=BLUE)
    return img


# ---------- 10 open book with A-Z ----------
def icon10():
    img = new()
    d = ImageDraw.Draw(img)
    cx = S / 2
    d.polygon([(28, 56), (cx, 74), (S - 28, 56), (S - 30, 150), (cx, 168), (30, 150)], fill=BLUE)
    d.polygon([(34, 64), (cx - 4, 80), (cx - 4, 156), (34, 142)], fill=WHITE)
    d.polygon([(S - 34, 64), (cx + 4, 80), (cx + 4, 156), (S - 34, 142)], fill=PAPER)
    d.line([(cx, 78), (cx, 158)], fill=BLUE_DK, width=3)
    d.text((cx - 58, 96), "A", font=f_arial_s, fill=BLUE)
    d.text((cx + 18, 96), "Z", font=f_arial_s, fill=BLUE)
    d.line([(cx - 58, 138), (cx - 14, 140)], fill=GREY, width=3)
    d.line([(cx + 14, 140), (cx + 58, 138)], fill=GREY, width=3)
    return img


generators = {
    "01_flat_book.png": icon01,
    "02_glossy_book.png": icon02,
    "03_book_magnifier.png": icon03,
    "04_closed_bookmark.png": icon04,
    "05_aa_type.png": icon05,
    "06_book_stack.png": icon06,
    "07_line_book.png": icon07,
    "08_pixel_book.png": icon08,
    "09_dict_block_ci.png": icon09,
    "10_az_book.png": icon10,
}

print("Generating 10 icons...")
for name, fn in generators.items():
    save(fn(), name)
print("Done.")
