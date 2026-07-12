"""Generate a clean, professional 1200x800 cover for 腕上词典 AstroBox v2.

Clean, modern app store style — no decorative clutter, 
bigger preview screenshots, better visual hierarchy.
"""

from PIL import Image, ImageDraw, ImageFont, ImageFilter
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
NAVY_MID = (6, 18, 42)
ACCENT = (29, 116, 232)
ACCENT_LIGHT = (70, 160, 255)
WHITE = (255, 255, 255)
GRAY = (160, 170, 190)
GRAY_DIM = (100, 110, 130)
DIM = (60, 70, 90)
CARD_BG = (16, 22, 44)

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


def create_cover():
    canvas = Image.new('RGBA', (W, H), (0, 0, 0, 0))
    draw = ImageDraw.Draw(canvas)

    # ===== 1. BACKGROUND =====
    # Smooth dark gradient: navy top -> slightly lighter bottom
    for y in range(H):
        t = y / H
        blend = 1 - math.cos(t * math.pi / 2)  # ease-out curve
        r = int(NAVY[0] + (NAVY_MID[0] - NAVY[0]) * blend)
        g = int(NAVY[1] + (NAVY_MID[1] - NAVY[1]) * blend)
        b = int(NAVY[2] + (NAVY_MID[2] - NAVY[2]) * blend)
        draw.line([(0, y), (W, y)], fill=(r, g, b))

    # Subtle ambient glow on right side only (no dots, no grid, no arcs)
    glow = Image.new('RGBA', (W, H), (0, 0, 0, 0))
    gdraw = ImageDraw.Draw(glow)
    for i in range(35):
        cx, cy = W - 120, H // 2
        rx, ry = 500 + i * 15, 380 + i * 10
        alpha = max(0, 15 - i // 3)
        gdraw.ellipse(
            [cx - rx, cy - ry, cx + rx, cy + ry],
            fill=(ACCENT[0], ACCENT[1], ACCENT[2], alpha)
        )
    canvas = Image.alpha_composite(canvas, glow)
    draw = ImageDraw.Draw(canvas)

    # ===== 2. ICON + TITLE (Left area) =====
    icon = Image.open(ICON).convert('RGBA')
    icon_size = 80
    icon_resized = icon.resize((icon_size, icon_size), Image.LANCZOS)
    ix, iy = 55, 55

    # Soft icon glow
    for s in range(10, 0, -2):
        draw.ellipse(
            [ix - s, iy - s, ix + icon_size + s, iy + icon_size + s],
            fill=(ACCENT[0], ACCENT[1], ACCENT[2], 20 - s)
        )
    canvas.paste(icon_resized, (ix, iy), icon_resized)

    # Title
    ft_t = load_font(FONT_BOLD, 48)
    ft_sub = load_font(FONT_EN_BOLD, 20)
    ft_tag = load_font(FONT_LIGHT, 18)

    tx = ix + icon_size + 18
    ty = iy + 4
    draw.text((tx, ty), '腕上词典', fill=WHITE, font=ft_t)
    draw.text((tx, ty + 52), 'Wrist Dictionary', fill=GRAY, font=ft_sub)
    draw.text((tx, ty + 78), '离线英汉词典 · 抬手即查', fill=ACCENT_LIGHT, font=ft_tag)

    # ===== 3. FEATURE BADGES =====
    ft_badge = load_font(FONT_BOLD, 16)
    badges = [
        ('📖', '15K+ 词库'),
        ('🌐', '英/中/日'),
        ('🔍', '模糊搜索'),
        ('🔄', '变形查词'),
        ('❤️', '收藏历史'),
        ('📡', '离线'),
    ]
    by0 = 175
    gap_x, gap_y = 12, 8

    # First row: 3 badges
    row1 = badges[:3]
    for i, (e, t) in enumerate(row1):
        full = f'{e} {t}'
        bb = draw.textbbox((0, 0), full, font=ft_badge)
        bw = bb[2] - bb[0] + 20
        bx = 55 + i * (145 + gap_x)
        rr(draw, [bx, by0, bx + bw, by0 + 30], r=15,
           fill=(ACCENT[0], ACCENT[1], ACCENT[2], 22),
           outline=(ACCENT[0], ACCENT[1], ACCENT[2], 50), width=1)
        draw.text((bx + 10, by0 + 4), full, fill=ACCENT_LIGHT, font=ft_badge)

    # Second row: 3 badges
    row2 = badges[3:]
    by1 = by0 + 30 + gap_y
    for i, (e, t) in enumerate(row2):
        full = f'{e} {t}'
        bb = draw.textbbox((0, 0), full, font=ft_badge)
        bw = bb[2] - bb[0] + 20
        bx = 55 + i * (145 + gap_x)
        rr(draw, [bx, by1, bx + bw, by1 + 30], r=15,
           fill=(ACCENT[0], ACCENT[1], ACCENT[2], 22),
           outline=(ACCENT[0], ACCENT[1], ACCENT[2], 50), width=1)
        draw.text((bx + 10, by1 + 4), full, fill=ACCENT_LIGHT, font=ft_badge)

    # ===== 4. PREVIEW SCREENSHOTS - 2x2 Grid (Right side) =====
    pw, ph = 176, 432  # maintain ~0.408 aspect ratio
    gap_s = 20
    gx0, gy0 = 530, 55
    corner_r = 12

    # Labels for each screenshot
    ft_label = load_font(FONT_REG, 13)
    labels = ['首页', '搜索', '英文结果', '中文结果']

    for i, pp in enumerate(PREVIEWS):
        col = i % 2
        row = i // 2
        px = gx0 + col * (pw + gap_s)
        py = gy0 + row * (ph + gap_s + 22)  # extra space for label

        img = Image.open(pp).convert('RGBA')
        img_resized = img.resize((pw, ph), Image.LANCZOS)

        # Card shadow (deeper)
        sd = Image.new('RGBA', (W, H), (0, 0, 0, 0))
        sdraw = ImageDraw.Draw(sd)
        for si in range(6, 0, -1):
            sdraw.rounded_rectangle(
                [px - si - 2, py - si - 2, px + pw + si + 2, py + ph + si + 2],
                radius=corner_r + 1, fill=(0, 0, 0, 18 + si * 4)
            )
        canvas = Image.alpha_composite(canvas, sd)
        draw = ImageDraw.Draw(canvas)

        # Card bezel
        card_pad = 4
        rr(draw, [px - card_pad, py - card_pad, px + pw + card_pad, py + ph + card_pad],
           r=corner_r + 1, fill=CARD_BG, outline=(40, 50, 75, 100), width=1)

        # Screenshot with rounded corners
        mask = Image.new('L', (pw, ph), 0)
        mdraw = ImageDraw.Draw(mask)
        mdraw.rounded_rectangle([(0, 0), (pw, ph)], radius=corner_r, fill=255)
        canvas.paste(img_resized, (px, py), mask)

        # Thin border
        rr(draw, [px, py, px + pw, py + ph], r=corner_r,
           outline=(255, 255, 255, 25), width=1)

        # Label below each screenshot
        lx = px + (pw - draw.textbbox((0, 0), labels[i], font=ft_label)[2] + draw.textbbox((0, 0), labels[i], font=ft_label)[0]) // 2
        ly = py + ph + 4
        draw.text((lx, ly), labels[i], fill=GRAY_DIM, font=ft_label)

    # ===== 5. DESCRIPTION =====
    ft_desc = load_font(FONT_REG, 15)
    desc_x = gx0
    desc_y = gy0 + 2 * (ph + 22 + gap_s) + 10
    desc = '小米手环上的离线词典 — 支持英语精确/前缀匹配、中文拼音输入、变形反查'
    draw.text((desc_x, desc_y), desc, fill=GRAY, font=ft_desc)

    # ===== 6. BOTTOM BAR =====
    bar_y = H - 38
    draw.line([(55, bar_y), (W - 55, bar_y)], fill=(255, 255, 255, 12))

    ft_footer = load_font(FONT_EN_LIGHT, 13)
    left = '腕上词典 v1.0.0  |  小米手环 Vela 快应用'
    right = '开源 github.com/pcai7296/wrist-dictionary'
    draw.text((55, bar_y + 8), left, fill=DIM, font=ft_footer)
    rbb = draw.textbbox((0, 0), right, font=ft_footer)
    draw.text((W - 55 - (rbb[2] - rbb[0]), bar_y + 8), right, fill=DIM, font=ft_footer)

    # ===== SAVE =====
    canvas.convert('RGB').save(OUT, 'PNG')
    sz = os.path.getsize(OUT)
    print(f'[OK] Cover saved: {OUT} ({W}x{H}, {sz/1024:.1f} KB)')
    return OUT


if __name__ == '__main__':
    create_cover()
