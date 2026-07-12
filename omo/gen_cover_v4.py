"""Generate refined 1200×800 cover for 腕上词典 — v4.
Addresses reviewer feedback:
- Fix badge text contrast (white on blue, not blue on blue)
- Remove 日 (app only supports 英/中)
- Icon: rounded-rect card instead of circle-behind-square
- Tighter layout, bigger screenshots that actually fit
"""

from PIL import Image, ImageDraw, ImageFont
import os, math

BASE = r'J:\code\MI band\腕上词典\release_repo'
OUT = os.path.join(BASE, 'cover.png')
ICON = os.path.join(BASE, 'icon.png')
PREVIEWS = [
    os.path.join(BASE, 'preview', '01_home.png'),
    os.path.join(BASE, 'preview', '02_search.png'),
    os.path.join(BASE, 'preview', '03_results_en.png'),
    os.path.join(BASE, 'preview', '04_results_zh.png'),
]

W, H = 1200, 800
NAVY = (2, 8, 19)
NAVY_MID = (8, 20, 48)
ACCENT = (29, 116, 232)
ACCENT_DARK = (18, 80, 180)
WHITE = (255, 255, 255)
GRAY = (160, 170, 190)
GRAY_DIM = (100, 110, 130)
DIM = (60, 70, 90)
CARD_BG = (14, 20, 42)

FONT_BOLD = r'C:\Windows\Fonts\msyhbd.ttc'
FONT_REG = r'C:\Windows\Fonts\msyh.ttc'
FONT_LIGHT = r'C:\Windows\Fonts\msyhl.ttc'
FONT_EN_BOLD = r'C:\Windows\Fonts\segoeuib.ttf'
FONT_EN = r'C:\Windows\Fonts\segoeui.ttf'
FONT_EN_LIGHT = r'C:\Windows\Fonts\segoeuil.ttf'


def load_font(path, size):
    try:
        return ImageFont.truetype(path, size)
    except:
        return ImageFont.load_default()


def rr(draw, xy, r, fill=None, outline=None, width=1):
    draw.rounded_rectangle(xy, radius=r, fill=fill, outline=outline, width=width)


def make_circular_icon(icon_img, size):
    """Mask icon to a circle with a blue border ring."""
    icon_img = icon_img.resize((size, size), Image.LANCZOS)
    mask = Image.new('L', (size, size), 0)
    mdraw = ImageDraw.Draw(mask)
    mdraw.ellipse([(0, 0), (size, size)], fill=255)
    result = Image.new('RGBA', (size, size), (0, 0, 0, 0))
    result.paste(icon_img, (0, 0), mask)
    return result, mask


def create_cover():
    canvas = Image.new('RGBA', (W, H), (0, 0, 0, 0))

    # ===== 1. BACKGROUND =====
    for y in range(H):
        t = y / H
        blend = 1 - math.cos(t * math.pi / 2)
        r = int(NAVY[0] + (NAVY_MID[0] - NAVY[0]) * blend)
        g = int(NAVY[1] + (NAVY_MID[1] - NAVY[1]) * blend)
        b = int(NAVY[2] + (NAVY_MID[2] - NAVY[2]) * blend)
        draw = ImageDraw.Draw(canvas)
        draw.line([(0, y), (W, y)], fill=(r, g, b))

    # Right-side ambient glow
    glow = Image.new('RGBA', (W, H), (0, 0, 0, 0))
    gdraw = ImageDraw.Draw(glow)
    for i in range(30):
        cx, cy = W - 100, H // 3
        rx, ry = 450 + i * 14, 350 + i * 10
        alpha = max(0, 18 - i // 2)
        gdraw.ellipse([cx - rx, cy - ry, cx + rx, cy + ry],
                      fill=(ACCENT[0], ACCENT[1], ACCENT[2], alpha))
    canvas = Image.alpha_composite(canvas, glow)

    # ===== 2. ICON (circular mask, no circle-behind-square) =====
    icon = Image.open(ICON).convert('RGBA')
    icon_size = 72
    circular_icon, icon_mask = make_circular_icon(icon, icon_size)
    ix, iy = 45, 42

    # Draw a subtle ring around the icon (thin, matches the accent)
    draw = ImageDraw.Draw(canvas)
    draw.ellipse([ix - 2, iy - 2, ix + icon_size + 2, iy + icon_size + 2],
                 outline=(ACCENT[0], ACCENT[1], ACCENT[2], 100), width=2)
    canvas.paste(circular_icon, (ix, iy), icon_mask)

    # ===== 3. TITLE =====
    ft_title = load_font(FONT_BOLD, 46)
    ft_sub = load_font(FONT_EN_BOLD, 20)
    ft_tag = load_font(FONT_LIGHT, 18)

    tx = ix + icon_size + 16
    ty = iy + 2
    draw.text((tx, ty), '腕上词典', fill=WHITE, font=ft_title)
    draw.text((tx, ty + 50), 'Wrist Dictionary', fill=GRAY, font=ft_sub)
    draw.text((tx, ty + 76), '离线英汉词典 · 抬手即查', fill=ACCENT, font=ft_tag)

    # ===== 4. FEATURE BADGES — white text, opaque blue bg =====
    ft_badge = load_font(FONT_BOLD, 16)
    badges = [
        ('📖', '15K+ 词库'),
        ('🌐', '英/中'),
        ('🔍', '模糊搜索'),
        ('🔄', '变形查词'),
        ('❤️', '收藏历史'),
        ('📡', '离线'),
    ]
    by0 = 170
    gap_x, gap_y = 10, 8

    for i, (e, t) in enumerate(badges):
        full = f'{e} {t}'
        bb = draw.textbbox((0, 0), full, font=ft_badge)
        bw = bb[2] - bb[0] + 24
        row = i // 3
        col = i % 3
        bx = 45 + col * (140 + gap_x)
        by = by0 + row * (32 + gap_y)

        # Opaque blue background for high contrast
        rr(draw, [bx, by, bx + bw, by + 30], r=15,
           fill=ACCENT_DARK, outline=ACCENT, width=1)
        # WHITE text (not blue-on-blue)
        draw.text((bx + 12, by + 5), full, fill=WHITE, font=ft_badge)

    # ===== 5. SHORT DESCRIPTION =====
    ft_desc = load_font(FONT_REG, 15)
    desc_y = by0 + 2 * (32 + gap_y) + 18
    desc = '15K 英文词条 · 128K 中文词组 · 模糊搜索 · 变形反查'
    draw.text((45, desc_y), desc, fill=GRAY, font=ft_desc)

    # ===== 6. 2×2 SCREENSHOT GRID (right side) =====
    # Calculate size that FITS within 800px height
    # Available: y=45 to y=750 = 705px, 2 rows + 16px gap
    # Each: (705 - 16) / 2 = 344.5 → 344
    ph = 340
    pw = int(ph * 212 / 520)  # = 138
    gap_s = 14
    gx0 = W - 2 * pw - gap_s - 50  # right-align with 50px margin
    gy0 = 45
    corner_r = 10

    ft_label = load_font(FONT_REG, 12)
    labels = ['首页', '搜索', '英文结果', '中文结果']

    for i, pp in enumerate(PREVIEWS):
        col = i % 2
        row = i // 2
        px = gx0 + col * (pw + gap_s)
        py = gy0 + row * (ph + gap_s + 18)

        img = Image.open(pp).convert('RGBA')
        img_resized = img.resize((pw, ph), Image.LANCZOS)

        # Shadow
        sd = Image.new('RGBA', (W, H), (0, 0, 0, 0))
        sdraw = ImageDraw.Draw(sd)
        for si in range(5, 0, -1):
            sdraw.rounded_rectangle(
                [px - si - 1, py - si - 1, px + pw + si + 1, py + ph + si + 1],
                radius=corner_r, fill=(0, 0, 0, 15 + si * 5))
        canvas = Image.alpha_composite(canvas, sd)
        draw = ImageDraw.Draw(canvas)

        # Card bezel
        rr(draw, [px - 3, py - 3, px + pw + 3, py + ph + 3],
           r=corner_r + 1, fill=CARD_BG, outline=(40, 50, 75, 80), width=1)

        # Screenshot with rounded corners
        mask = Image.new('L', (pw, ph), 0)
        mdraw = ImageDraw.Draw(mask)
        mdraw.rounded_rectangle([(0, 0), (pw, ph)], radius=corner_r, fill=255)
        canvas.paste(img_resized, (px, py), mask)

        # Thin border
        rr(draw, [px, py, px + pw, py + ph], r=corner_r,
           outline=(255, 255, 255, 20), width=1)

        # Label
        lx = px + (pw - (draw.textbbox((0, 0), labels[i], font=ft_label)[2] -
                         draw.textbbox((0, 0), labels[i], font=ft_label)[0])) // 2
        ly = py + ph + 4
        draw.text((lx, ly), labels[i], fill=GRAY_DIM, font=ft_label)

    # ===== 7. BOTTOM BAR =====
    bar_y = H - 36
    draw.line([(45, bar_y), (W - 45, bar_y)], fill=(255, 255, 255, 10))

    ft_footer = load_font(FONT_EN_LIGHT, 12)
    left = '腕上词典 v1.0.0  |  小米手环 Vela 快应用'
    right = '开源 github.com/pcai7296/wrist-dictionary'
    draw.text((45, bar_y + 7), left, fill=DIM, font=ft_footer)
    rbb = draw.textbbox((0, 0), right, font=ft_footer)
    draw.text((W - 45 - (rbb[2] - rbb[0]), bar_y + 7), right, fill=DIM, font=ft_footer)

    # ===== SAVE =====
    canvas.convert('RGB').save(OUT, 'PNG')
    sz = os.path.getsize(OUT)
    print(f'[OK] Cover saved: {OUT} ({W}x{H}, {sz/1024:.1f} KB)')


if __name__ == '__main__':
    create_cover()
