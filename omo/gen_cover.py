"""Generate a 1200x800 cover image for 腕上词典 (Wrist Dictionary)
AstroBox submission, using existing preview screenshots and icon."""

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
BG = (2, 8, 19)          # #020813
ACCENT = (29, 116, 232)  # #1d74e8
ACCENT_DIM = (20, 80, 180)
WHITE = (255, 255, 255)
GRAY = (160, 170, 190)
DIM = (60, 70, 90)

# Font paths
FONT_BOLD = r'C:\Windows\Fonts\msyhbd.ttc'
FONT_REG = r'C:\Windows\Fonts\msyh.ttc'
FONT_LIGHT = r'C:\Windows\Fonts\msyhl.ttc'
FONT_EN_BOLD = r'C:\Windows\Fonts\segoeuib.ttf'
FONT_EN = r'C:\Windows\Fonts\segoeui.ttf'

def rounded_rect(draw, xy, r, fill=None, outline=None, width=1):
    """Draw a rounded rectangle."""
    x1, y1, x2, y2 = xy
    draw.rounded_rectangle(xy, radius=r, fill=fill, outline=outline, width=width)

def create_cover():
    canvas = Image.new('RGBA', (W, H), (0, 0, 0, 0))
    draw = ImageDraw.Draw(canvas)

    # 1. Background: dark with radial gradient effect
    bg = Image.new('RGBA', (W, H), BG)
    for y in range(H):
        t = y / H
        r = int(2 + 6 * (1 - t))
        g = int(8 + 12 * (1 - t))
        b = int(19 + 25 * (1 - t))
        draw.line([(0, y), (W, y)], fill=(r, g, b))
    
    # 2. Subtle blue glow on the right side
    glow = Image.new('RGBA', (W, H), (0, 0, 0, 0))
    gdraw = ImageDraw.Draw(glow)
    for i in range(30):
        cx, cy = W - 100, H // 2
        radius = 600 + i * 15
        alpha = max(0, 12 - i)
        gdraw.ellipse(
            [cx - radius, cy - radius, cx + radius, cy + radius],
            fill=(29, 116, 232, alpha)
        )
    canvas = Image.alpha_composite(canvas, glow)
    draw = ImageDraw.Draw(canvas)

    # 3. Grid lines (subtle)
    for x in range(0, W, 60):
        draw.line([(x, 0), (x, H)], fill=(255, 255, 255, 3))
    for y in range(0, H, 60):
        draw.line([(0, y), (W, y)], fill=(255, 255, 255, 3))

    # 4. Load & paste icon (top-left area)
    icon = Image.open(ICON).convert('RGBA')
    icon_size = 88
    icon_resized = icon.resize((icon_size, icon_size), Image.LANCZOS)
    icon_x, icon_y = 55, 48
    # Icon background circle
    draw.ellipse(
        [icon_x - 6, icon_y - 6, icon_x + icon_size + 6, icon_y + icon_size + 6],
        fill=(255, 255, 255, 30)
    )
    canvas.paste(icon_resized, (icon_x, icon_y), icon_resized)

    # 5. Title
    try:
        font_title = ImageFont.truetype(FONT_BOLD, 52)
        font_sub = ImageFont.truetype(FONT_EN, 22)
        font_tagline = ImageFont.truetype(FONT_REG, 24)
        font_feature = ImageFont.truetype(FONT_REG, 20)
        font_en_sm = ImageFont.truetype(FONT_EN, 18)
        font_badge = ImageFont.truetype(FONT_BOLD, 16)
        font_footer = ImageFont.truetype(FONT_REG, 14)
    except:
        font_title = ImageFont.load_default()
        font_sub = font_title
        font_tagline = font_title
        font_feature = font_title
        font_en_sm = font_title
        font_badge = font_title
        font_footer = font_title

    title_x = icon_x + icon_size + 20
    title_y = icon_y + 4
    draw.text((title_x, title_y), '腕上词典', fill=WHITE, font=font_title)
    
    sub_y = title_y + 56
    draw.text((title_x, sub_y), 'Wrist Dictionary', fill=GRAY, font=font_sub)
    
    # Tagline
    tag_y = sub_y + 32
    draw.text((title_x, tag_y), '离线英汉词典 · 抬手即查', fill=ACCENT, font=font_tagline)

    # 6. Feature badges row (below title area)
    features = ['📖 15K+ 词库', '🌐 英/中/日', '🔍 模糊搜索', '❤️ 收藏历史', '📡 离线']
    badge_y = 190
    badge_x_start = 55
    badge_h = 32
    for i, feat in enumerate(features):
        bx = badge_x_start + i * 145
        # badge background
        draw.rounded_rectangle(
            [bx, badge_y, bx + 135, badge_y + badge_h],
            radius=16, fill=(29, 116, 232, 40), outline=(29, 116, 232, 80), width=1
        )
        # badge text (skip emoji, use text only)
        text_only = feat.split(' ')[-1] if ' ' in feat else feat
        draw.text((bx + 10, badge_y + 5), feat, fill=ACCENT, font=font_badge)

    # 7. Preview screenshots - 2x2 grid on the right side
    preview_size = (160, 393)  # maintaining 212:520 aspect ratio ~ 0.407
    grid_x_start = 500
    grid_y_start = 90
    gap = 22
    corner_r = 12
    
    for i, pp in enumerate(PREVIEWS):
        col = i % 2
        row = i // 2
        px = grid_x_start + col * (preview_size[0] + gap)
        py = grid_y_start + row * (preview_size[1] + gap)
        
        img = Image.open(pp).convert('RGBA')
        img_resized = img.resize(preview_size, Image.LANCZOS)
        
        # Create rounded corners mask
        mask = Image.new('L', preview_size, 0)
        mdraw = ImageDraw.Draw(mask)
        mdraw.rounded_rectangle([(0, 0), preview_size], radius=corner_r, fill=255)
        
        # Apply subtle shadow effect
        shadow_offset = 3
        shadow = Image.new('RGBA', preview_size, (0, 0, 0, 0))
        sdraw = ImageDraw.Draw(shadow)
        sdraw.rounded_rectangle(
            [(shadow_offset, shadow_offset), (preview_size[0], preview_size[1])],
            radius=corner_r, fill=(0, 0, 0, 60)
        )
        canvas.paste(shadow, (px, py), mask)
        
        # Paste screenshot
        canvas.paste(img_resized, (px, py), mask)
        
        # Outer border
        draw.rounded_rectangle(
            [px, py, px + preview_size[0], py + preview_size[1]],
            radius=corner_r, outline=(255, 255, 255, 40), width=1
        )

    # 8. App description box (below previews)
    desc_x = grid_x_start
    desc_y = grid_y_start + 2 * (preview_size[1] + gap) + 15
    desc = '小米手环上的离线词典 — 支持英语精确/前缀匹配、中文\n拼音输入、变形反查，约15K英文词条 + 128K中文词组'
    draw.text((desc_x, desc_y), desc, fill=GRAY, font=font_en_sm)

    # 9. Bottom bar
    bar_y = H - 42
    draw.line([(0, bar_y), (W, bar_y)], fill=(255, 255, 255, 15))
    draw.text((55, bar_y + 10), '腕上词典  |  小米手环 Vela 快应用', fill=DIM, font=font_footer)
    draw.text((W - 300, bar_y + 10), '开源 github.com/pcai7296/wrist-dictionary', fill=DIM, font=font_footer)

    # 10. Save
    canvas = canvas.convert('RGB')
    canvas.save(OUT, 'PNG')
    print(f'Cover saved: {OUT} ({W}x{H})')
    return OUT

if __name__ == '__main__':
    create_cover()
