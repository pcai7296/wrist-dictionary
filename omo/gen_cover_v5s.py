"""Cover v5-Slim — 针对审核要求：去繁就简，提升质感"""

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
ACCENT = (29, 116, 232)
ACCENT_DARK = (18, 80, 180)
WHITE = (255, 255, 255)
GRAY = (160, 170, 190)
CARD_BG = (14, 20, 42)

FONT_BOLD = r'C:\Windows\Fonts\msyhbd.ttc'
FONT_REG = r'C:\Windows\Fonts\msyh.ttc'
FONT_LIGHT = r'C:\Windows\Fonts\msyhl.ttc'

def load_font(path, size):
    try: return ImageFont.truetype(path, size)
    except: return ImageFont.load_default()

def rr(draw, xy, r, fill=None, outline=None, width=1):
    draw.rounded_rectangle(xy, radius=r, fill=fill, outline=outline, width=width)

def make_circular_icon(icon_img, size):
    icon_img = icon_img.resize((size, size), Image.LANCZOS)
    mask = Image.new('L', (size, size), 0)
    ImageDraw.Draw(mask).ellipse([(0, 0), (size, size)], fill=255)
    result = Image.new('RGBA', (size, size), (0, 0, 0, 0))
    result.paste(icon_img, (0, 0), mask)
    return result, mask

def create_cover():
    canvas = Image.new('RGBA', (W, H), NAVY)
    draw = ImageDraw.Draw(canvas)

    # ===== 1. 简化背景：去掉复杂渐变和光晕，保留纯色质感 =====
    glow = Image.new('RGBA', (W, H), (0, 0, 0, 0))
    gdraw = ImageDraw.Draw(glow)
    gdraw.ellipse([W-400, -200, W+100, 300], fill=(ACCENT[0], ACCENT[1], ACCENT[2], 15))
    canvas = Image.alpha_composite(canvas, glow)
    draw = ImageDraw.Draw(canvas)

    # ===== 2. 头部区域：紧凑排列 =====
    icon = Image.open(ICON).convert('RGBA')
    icon_size = 56
    circular_icon, icon_mask = make_circular_icon(icon, icon_size)
    ix, iy = 48, 36
    canvas.paste(circular_icon, (ix, iy), icon_mask)

    ft_t = load_font(FONT_BOLD, 36)
    ft_s = load_font(FONT_REG, 16)
    tx = ix + icon_size + 16
    ty = iy + 4
    draw.text((tx, ty), '腕上词典', fill=WHITE, font=ft_t)
    draw.text((tx, ty + 40), '离线英汉词典 · 抬手即查', fill=GRAY, font=ft_s)

    # ===== 3. 核心卖点：仅保留最关键的3个 =====
    ft_badge = load_font(FONT_BOLD, 14)
    badges = ['词库15K+', '智能容错', '完全离线']

    bx = 48
    by = 115
    for txt in badges:
        bb = draw.textbbox((0, 0), txt, font=ft_badge)
        bw = bb[2] - bb[0] + 18
        rr(draw, [bx, by, bx + bw, by + 26], r=13, fill=ACCENT_DARK)
        draw.text((bx + 9, by + 3), txt, fill=WHITE, font=ft_badge)
        bx += bw + 10

    # ===== 4. 截图区域：放大，减少上下留白 =====
    ss_h = 560
    ss_w = int(ss_h * 212 / 520)
    gap_ss = 14
    total_w = 4 * ss_w + 3 * gap_ss
    ss_x0 = (W - total_w) // 2
    ss_y0 = 155
    cr = 10

    labels = ['首页', '搜索', '英文结果', '中文结果']
    ft_label = load_font(FONT_REG, 13)

    for i, pp in enumerate(PREVIEWS):
        sx = ss_x0 + i * (ss_w + gap_ss)
        sy = ss_y0

        img = Image.open(pp).convert('RGBA')
        img_resized = img.resize((ss_w, ss_h), Image.LANCZOS)

        rr(draw, [sx-3, sy-3, sx+ss_w+3, sy+ss_h+3], r=cr+1, fill=(0,0,0,40))
        rr(draw, [sx-2, sy-2, sx+ss_w+2, sy+ss_h+2], r=cr, fill=CARD_BG)

        mask = Image.new('L', (ss_w, ss_h), 0)
        ImageDraw.Draw(mask).rounded_rectangle([(0,0),(ss_w,ss_h)], radius=cr, fill=255)
        canvas.paste(img_resized, (sx, sy), mask)

        lbb = draw.textbbox((0, 0), labels[i], font=ft_label)
        draw.text((sx + (ss_w - lbb[2])/2, sy + ss_h + 8), labels[i], fill=GRAY, font=ft_label)

    # ===== 5. 底部信息：极度精简 =====
    ft_foot = load_font(FONT_LIGHT, 11)
    footer = '腕上词典 v1.0.0 · 小米手环 Vela 快应用'
    draw.text((48, H - 28), footer, fill=(90, 100, 120), font=ft_foot)

    canvas.convert('RGB').save(OUT, 'PNG')
    print(f'[OK] Cover saved: {OUT}')

if __name__ == '__main__':
    create_cover()
