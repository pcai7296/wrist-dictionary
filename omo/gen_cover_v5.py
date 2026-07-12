"""Cover v5 — fixes emoji rendering, 4 screenshots in one row at bottom."""

from PIL import Image, ImageDraw, ImageFont
import os, math, textwrap

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
    icon_img = icon_img.resize((size, size), Image.LANCZOS)
    mask = Image.new('L', (size, size), 0)
    mdraw = ImageDraw.Draw(mask)
    mdraw.ellipse([(0, 0), (size, size)], fill=255)
    result = Image.new('RGBA', (size, size), (0, 0, 0, 0))
    result.paste(icon_img, (0, 0), mask)
    return result, mask


def create_cover():
    canvas = Image.new('RGBA', (W, H), (0, 0, 0, 0))

    # ===== 1. GRADIENT BACKGROUND =====
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
    draw = ImageDraw.Draw(canvas)

    # ===== 2. ICON — circular with thin accent ring =====
    icon = Image.open(ICON).convert('RGBA')
    icon_size = 64
    circular_icon, icon_mask = make_circular_icon(icon, icon_size)
    ix, iy = 48, 24
    draw.ellipse([ix - 2, iy - 2, ix + icon_size + 2, iy + icon_size + 2],
                 outline=(ACCENT[0], ACCENT[1], ACCENT[2], 120), width=2)
    canvas.paste(circular_icon, (ix, iy), icon_mask)

    # ===== 3. TITLE =====
    ft_t = load_font(FONT_BOLD, 38)
    ft_s = load_font(FONT_REG, 16)  # msyh has both EN and CJK glyphs
    ft_tag = load_font(FONT_LIGHT, 15)

    tx = ix + icon_size + 14
    ty = iy + 2
    draw.text((tx, ty), '腕上词典', fill=WHITE, font=ft_t)
    draw.text((tx, ty + 42), 'Wrist Dictionary · 离线英汉词典 · 抬手即查',
              fill=GRAY, font=ft_s)

    # ===== 4. FEATURE BADGES — no emoji, pure text =====
    ft_b = load_font(FONT_BOLD, 15)
    badges = ['词库15K+', '英/中', '模糊搜索', '变形查词', '收藏历史', '离线']

    by0 = 108
    gap_bx = 8
    bx = 48
    for t in badges:
        bb = draw.textbbox((0, 0), t, font=ft_b)
        bw = bb[2] - bb[0] + 20
        rr(draw, [bx, by0, bx + bw, by0 + 28], r=14,
           fill=ACCENT_DARK, outline=(ACCENT[0], ACCENT[1], ACCENT[2], 50), width=1)
        draw.text((bx + 10, by0 + 4), t, fill=WHITE, font=ft_b)
        bx += bw + gap_bx

    # ===== 5. PRODUCT INTRO — continuous paragraphs in top-right =====
    ft_pi = load_font(FONT_REG, 15)
    intro_paras = [
        '腕上词典将精选词库完整装入你的手腕，无需网络即可随时随',
        '地查询英语单词和中文释义。查词结果清晰呈现词性、音标与',
        '多义项，日常学习阅读中遇到生词抬手就能解决。',
        '',
        '应用内置智能反查与容错匹配功能，无论是动词时态、形容词',
        '变形还是拼写偏差都能快速定位到正确词条。所有查词记录自',
        '动保存，生词可一键收藏，让英语学习更加高效便捷。',
    ]
    pi_x = 600
    pi_y = 20
    for line in intro_paras:
        if line:
            draw.text((pi_x, pi_y), line, fill=GRAY, font=ft_pi)
        pi_y += 21

    # Divider line
    draw.line([(48, 175), (W - 48, 175)], fill=(255, 255, 255, 12))

    # ===== 6. 4 SCREENSHOTS IN ONE ROW AT BOTTOM =====
    # Calculate size: fit 4 in a row
    ss_h = 530
    ss_w = int(ss_h * 212 / 520)  # 216
    gap_ss = 12
    total_w = 4 * ss_w + 3 * gap_ss
    ss_x0 = (W - total_w) // 2
    ss_y0 = 190
    cr = 8

    ft_l = load_font(FONT_REG, 12)
    labels = ['首页', '搜索', '英文结果', '中文结果']

    for i, pp in enumerate(PREVIEWS):
        sx = ss_x0 + i * (ss_w + gap_ss)
        sy = ss_y0

        img = Image.open(pp).convert('RGBA')
        img_resized = img.resize((ss_w, ss_h), Image.LANCZOS)

        # Shadow
        sd = Image.new('RGBA', (W, H), (0, 0, 0, 0))
        sdraw = ImageDraw.Draw(sd)
        for si in range(4, 0, -1):
            sdraw.rounded_rectangle(
                [sx - si, sy - si, sx + ss_w + si, sy + ss_h + si],
                radius=cr, fill=(0, 0, 0, 12 + si * 4))
        canvas = Image.alpha_composite(canvas, sd)
        draw = ImageDraw.Draw(canvas)

        # Card bg
        rr(draw, [sx - 2, sy - 2, sx + ss_w + 2, sy + ss_h + 2],
           r=cr + 1, fill=CARD_BG, outline=(40, 50, 75, 60), width=1)

        # Screenshot with rounded corners
        mask = Image.new('L', (ss_w, ss_h), 0)
        mdraw = ImageDraw.Draw(mask)
        mdraw.rounded_rectangle([(0, 0), (ss_w, ss_h)], radius=cr, fill=255)
        canvas.paste(img_resized, (sx, sy), mask)

        # Border
        rr(draw, [sx, sy, sx + ss_w, sy + ss_h], r=cr,
           outline=(255, 255, 255, 15), width=1)

        # Label
        lbb = draw.textbbox((0, 0), labels[i], font=ft_l)
        lw = lbb[2] - lbb[0]
        lx = sx + (ss_w - lw) // 2
        ly = sy + ss_h + 5
        draw.text((lx, ly), labels[i], fill=GRAY, font=ft_l)

    # ===== 7. INFO BAR (bottom) =====
    bar_y = H - 38
    draw.line([(48, bar_y), (W - 48, bar_y)], fill=(255, 255, 255, 8))

    ft_f = load_font(FONT_LIGHT, 12)
    left = '腕上词典 v1.0.0  |  小米手环 Vela 快应用'
    right = 'github.com/pcai7296/wrist-dictionary'
    draw.text((48, bar_y + 8), left, fill=GRAY_DIM, font=ft_f)
    rbb = draw.textbbox((0, 0), right, font=ft_f)
    draw.text((W - 48 - (rbb[2] - rbb[0]), bar_y + 8), right, fill=GRAY_DIM, font=ft_f)

    # ===== SAVE =====
    canvas.convert('RGB').save(OUT, 'PNG')
    sz = os.path.getsize(OUT)
    print(f'[OK] v5 cover: {OUT}  ({W}x{H}, {sz/1024:.1f} KB)')
    print(f'  Screenshots: {ss_w}x{ss_h}px each, 4 in row at y={ss_y0}, total width={total_w}')


if __name__ == '__main__':
    create_cover()
