"""Generate 24x24 blue button icons for home page"""
import math, os
from PIL import Image, ImageDraw

OUT = r"J:\code\MI band\腕上词典\src\common\icons"
BLUE = (29, 116, 232, 255)
S = 48  # 2x for smoothness

def new():
    return Image.new("RGBA", (S, S), (0, 0, 0, 0))

def save(img, name):
    img = img.resize((24, 24), Image.LANCZOS)
    path = f"{OUT}/{name}"
    img.save(path)
    print(f"  {name}: {os.path.getsize(path)} bytes")

# 1. 查找变形 — cycle arrow
def icon_transform():
    img = new()
    d = ImageDraw.Draw(img)
    d.arc([8, 8, 40, 40], start=40, end=310, fill=BLUE, width=6)
    d.polygon([(36, 12), (30, 20), (38, 18)], fill=BLUE)
    return img

# 2. 中英查找 — magnifier
def icon_search():
    img = new()
    d = ImageDraw.Draw(img)
    d.ellipse([10, 8, 34, 32], outline=BLUE, width=5)
    d.line([(30, 28), (40, 40)], fill=BLUE, width=5)
    return img

# 3. 历史记录 — clock
def icon_history():
    img = new()
    d = ImageDraw.Draw(img)
    cx, cy = S/2, S/2
    d.ellipse([6, 6, 42, 42], outline=BLUE, width=4)
    d.line([(cx, cy), (cx, cy - 14)], fill=BLUE, width=4)
    d.line([(cx, cy), (cx + 10, cy + 4)], fill=BLUE, width=3)
    return img

# 4. 我的收藏 — ★ hollow star
def icon_fav():
    img = new()
    d = ImageDraw.Draw(img)
    cx, cy = S/2, S/2
    r_o, r_i = 20, 9
    pts = []
    for i in range(10):
        a = -90 + i * 36
        r = r_o if i % 2 == 0 else r_i
        pts.append((cx + r * math.cos(math.radians(a)), cy + r * math.sin(math.radians(a))))
    d.polygon(pts, outline=BLUE, width=4)
    return img

# 5. 关于 — "i" in circle
def icon_about():
    img = new()
    d = ImageDraw.Draw(img)
    d.ellipse([6, 6, 42, 42], outline=BLUE, width=4)
    d.ellipse([21, 11, 27, 17], fill=BLUE)
    d.rectangle([22, 20, 26, 34], fill=BLUE)
    return img

# 6. 赞助 — heart
def icon_sponsor():
    img = new()
    d = ImageDraw.Draw(img)
    pts = []
    for t in range(0, 360):
        a = math.radians(t)
        x = 16 * math.sin(a) ** 3
        y = 13 * math.cos(a) - 5 * math.cos(2 * a) - 2 * math.cos(3 * a) - math.cos(4 * a)
        pts.append((24 + x * 1.15, 28 + y * 1.2))
    d.polygon(pts, fill=BLUE)
    return img

items = {
    "btn_transform.png": icon_transform,
    "btn_search.png": icon_search,
    "btn_history.png": icon_history,
    "btn_fav.png": icon_fav,
    "btn_about.png": icon_about,
    "btn_sponsor.png": icon_sponsor,
}
print("Generating button icons...")
for name, fn in items.items():
    save(fn(), name)
print("Done")
