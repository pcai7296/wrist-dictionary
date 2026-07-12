"""Generate a professional 1200x800 cover image for 腕上词典 AstroBox v2 submission.

Uses Python Pillow to create a commercial-grade cover with:
- Radial gradient background with subtle decorative elements
- Card-based preview screenshots with depth
- Professional typography with proper hierarchy
- Feature badges and metadata

Requirements: pip install Pillow
"""

from PIL import Image, ImageDraw, ImageFont, ImageFilter, ImageOps
import os, math, random

random.seed(42)

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
BG_DEEP = (2, 8, 19)
BG_MID = (5, 16, 38)
ACCENT = (29, 116, 232)       # #1d74e8
ACCENT_LIGHT = (60, 150, 255)
ACCENT_GLOW = (29, 116, 232)
WHITE = (255, 255, 255)
GRAY_LIGHT = (200, 210, 225)
GRAY = (160, 170, 190)
GRAY_DIM = (100, 110, 130)
DIM = (60, 70, 90)

# Font paths
FONT_BOLD = r'C:\Windows\Fonts\msyhbd.ttc'
FONT_REG = r'C:\Windows\Fonts\msyh.ttc'
FONT_LIGHT = r'C:\Windows\Fonts\msyhl.ttc'
FONT_EN_BOLD = r'C:\Windows\Fonts\segoeuib.ttf'
FONT_EN = r'C:\Windows\Fonts\segoeui.ttf'
FONT_EN_LIGHT = r'C:\Windows\Fonts\segoeuil.ttf'


def hex_to_rgb(h):
    h = h.lstrip('#')
    return tuple(int(h[i:i+2], 16) for i in (0, 2, 4))


def load_font(path, size):
    try:
        return ImageFont.truetype(path, size)
    except Exception:
        return ImageFont.load_default()


def create_radial_gradient(w, h, center, inner_color, outer_color):
    """Create a radial gradient image."""
    img = Image.new('RGBA', (w, h), (0, 0, 0, 0))
    cx, cy = center
    max_dist = math.sqrt(max(cx, w-cx)**2 + max(cy, h-cy)**2)
    for y in range(h):
        for x in range(w):
            dx = x - cx
            dy = y - cy
            dist = math.sqrt(dx*dx + dy*dy)
            t = min(1.0, dist / max_dist)
            r = int(inner_color[0] + (outer_color[0] - inner_color[0]) * t)
            g = int(inner_color[1] + (outer_color[1] - inner_color[1]) * t)
            b = int(inner_color[2] + (outer_color[2] - inner_color[2]) * t)
            a_val = int(inner_color[3] if len(inner_color) > 3 else 255 + (outer_color[3] if len(outer_color) > 3 else 255 - (inner_color[3] if len(inner_color) > 3 else 255)) * t)
            img.putpixel((x, y), (r, g, b, a_val if len(inner_color) > 3 else 255))
    return img


def draw_rounded_rect(draw, xy, r, fill=None, outline=None, width=1):
    """Draw a rounded rectangle."""
    x1, y1, x2, y2 = xy
    draw.rounded_rectangle(xy, radius=r, fill=fill, outline=outline, width=width)


def create_cover():
    canvas = Image.new('RGBA', (W, H), (0, 0, 0, 0))

    # ============================================================
    # 1. BACKGROUND GRADIENT
    # ============================================================
    bg = Image.new('RGBA', (W, H), BG_DEEP)

    # Vertical gradient: deep navy top -> slightly lighter bottom
    for y in range(H):
        t = y / H
        r = int(BG_DEEP[0] + (BG_MID[0] - BG_DEEP[0]) * (1 - math.cos(t * math.pi / 2)))
        g = int(BG_DEEP[1] + (BG_MID[1] - BG_DEEP[1]) * (1 - math.cos(t * math.pi / 2)))
        b = int(BG_DEEP[2] + (BG_MID[2] - BG_DEEP[2]) * (1 - math.cos(t * math.pi / 2)))
        for x in range(W):
            bg.putpixel((x, y), (r, g, b))

    canvas.paste(bg, (0, 0))

    # Radial glow on right side
    glow_canvas = Image.new('RGBA', (W, H), (0, 0, 0, 0))
    gdraw = ImageDraw.Draw(glow_canvas)
    for i in range(40):
        cx, cy = W - 80, H // 3
        rx, ry = 550 + i * 18, 400 + i * 12
        alpha = max(0, 14 - i // 3)
        gdraw.ellipse(
            [cx - rx, cy - ry, cx + rx, cy + ry],
            fill=(29, 116, 232, alpha)
        )
    # Second glow - bottom left
    for i in range(25):
        cx, cy = 200, H - 50
        radius = 300 + i * 12
        alpha = max(0, 8 - i // 3)
        gdraw.ellipse(
            [cx - radius, cy - radius, cx + radius, cy + radius],
            fill=(29, 80, 200, alpha)
        )
    canvas = Image.alpha_composite(canvas, glow_canvas)

    # ============================================================
    # 2. DECORATIVE ELEMENTS
    # ============================================================
    decor = Image.new('RGBA', (W, H), (0, 0, 0, 0))
    ddraw = ImageDraw.Draw(decor)

    # Subtle grid lines (very faint)
    grid_color = (255, 255, 255, 4)
    for x in range(0, W, 40):
        ddraw.line([(x, 0), (x, H)], fill=grid_color)
    for y in range(0, H, 40):
        ddraw.line([(0, y), (W, y)], fill=grid_color)

    # Floating decorative dots
    dot_positions = [
        (950, 80, 3), (1050, 150, 2), (1100, 50, 4),
        (80, 180, 2), (150, 120, 3), (30, 300, 2),
        (1120, 350, 2), (980, 280, 3), (1080, 450, 2),
        (50, 600, 3), (120, 700, 2), (1000, 600, 2),
    ]
    for dx, dy, dr in dot_positions:
        ddraw.ellipse(
            [dx - dr, dy - dr, dx + dr, dy + dr],
            fill=(29, 116, 232, 20 + dr * 8)
        )

    # Decorative thin arc lines
    arc_color = (29, 116, 232, 15)
    ddraw.arc([-100, -50, 1300, 400], 0, 180, fill=arc_color, width=1)
    ddraw.arc([-50, -30, 1250, 420], 10, 170, fill=arc_color, width=1)

    canvas = Image.alpha_composite(canvas, decor)
    draw = ImageDraw.Draw(canvas)

    # ============================================================
    # 3. LOAD FONTS
    # ============================================================
    ft_bold_cn = load_font(FONT_BOLD, 54)
    ft_bold_cn_sm = load_font(FONT_BOLD, 22)
    ft_reg_cn = load_font(FONT_REG, 22)
    ft_reg_cn_sm = load_font(FONT_REG, 18)
    ft_reg_cn_xs = load_font(FONT_REG, 14)
    ft_light_cn = load_font(FONT_LIGHT, 20)
    ft_en_bold = load_font(FONT_EN_BOLD, 24)
    ft_en = load_font(FONT_EN, 18)
    ft_en_sm = load_font(FONT_EN, 15)
    ft_en_light = load_font(FONT_EN_LIGHT, 22)
    ft_en_light_sm = load_font(FONT_EN_LIGHT, 14)

    # ============================================================
    # 4. ICON + TITLE AREA (Left side)
    # ============================================================
    icon = Image.open(ICON).convert('RGBA')
    icon_size = 88
    icon_resized = icon.resize((icon_size, icon_size), Image.LANCZOS)
    icon_x, icon_y = 52, 48

    # Icon glow background
    for i in range(3):
        gs = 10 - i * 3
        draw.ellipse(
            [icon_x - gs, icon_y - gs, icon_x + icon_size + gs, icon_y + icon_size + gs],
            fill=(29, 116, 232, 25 - i * 7)
        )

    # Icon subtle border
    draw.ellipse(
        [icon_x - 4, icon_y - 4, icon_x + icon_size + 4, icon_y + icon_size + 4],
        outline=(255, 255, 255, 30), width=1
    )
    canvas.paste(icon_resized, (icon_x, icon_y), icon_resized)

    # Title
    title_x = icon_x + icon_size + 22
    title_y = icon_y + 4

    # "腕上词典" with slight shadow for depth
    shadow_offset = 1
    draw.text((title_x + shadow_offset, title_y + shadow_offset), '腕上词典', fill=(0, 0, 0, 80), font=ft_bold_cn)
    draw.text((title_x, title_y), '腕上词典', fill=WHITE, font=ft_bold_cn)

    # Subtitle "Wrist Dictionary"
    sub_y = title_y + 60
    draw.text((title_x, sub_y), 'Wrist Dictionary', fill=GRAY, font=ft_en_bold)

    # Tagline
    tag_y = sub_y + 34
    draw.text((title_x, tag_y), '离线英汉词典 · 抬手即查', fill=ACCENT_LIGHT, font=ft_light_cn)

    # ============================================================
    # 5. FEATURE BADGES
    # ============================================================
    features = [
        ('📖', '15K+ 词库'),
        ('🌐', '英/中/日'),
        ('🔍', '模糊搜索'),
        ('❤️', '收藏历史'),
        ('🔄', '变形查词'),
        ('📡', '离线'),
    ]

    badge_y = 205
    badge_x_start = 52
    badge_h = 34
    badge_gap = 10

    for i, (emoji, text) in enumerate(features):
        # Calculate text width for badge sizing
        full_text = f'{emoji} {text}'
        bbox = draw.textbbox((0, 0), full_text, font=ft_bold_cn_sm)
        tw = bbox[2] - bbox[0]
        bw = tw + 20  # padding 10px each side

        bx = badge_x_start + i * (130 if i < 3 else 128)
        if i >= 3:
            bx = badge_x_start + (i - 3) * (130 if i - 3 < 3 else 128)
            # Actually, let's do two rows
            pass

    # Recalculate: two rows of 3 badges
    row1_y = badge_y
    row2_y = badge_y + badge_h + 8
    badge_widths = [135, 120, 135, 120, 120, 95]  # proportional widths
    for i, (emoji, text) in enumerate(features):
        row = i // 3
        col = i % 3
        bx = badge_x_start + col * 145
        by = row1_y if row == 0 else row2_y
        bw = badge_widths[i]

        # Badge background - glass morphism style
        draw_rounded_rect(draw, [bx, by, bx + bw, by + badge_h], r=17,
                          fill=(29, 116, 232, 25),
                          outline=(29, 116, 232, 60), width=1)

        # Badge inner glow (subtle)
        draw_rounded_rect(draw, [bx + 2, by + 2, bx + bw - 2, by + badge_h - 2], r=15,
                          fill=(29, 116, 232, 10))

        # Badge text
        full_text = f'{emoji} {text}'
        draw.text((bx + 10, by + 5), full_text, fill=ACCENT_LIGHT, font=ft_bold_cn_sm)

    # ============================================================
    # 6. PREVIEW SCREENSHOTS - 2x2 Grid (Right side)
    # ============================================================
    preview_w = 168    # Width maintaining 212:520 ~ 0.408 aspect
    preview_h = int(preview_w / (212/520))  # ~412
    grid_x_start = 520
    grid_y_start = 65
    gap = 24
    corner_r = 14

    # Pre-compute layout
    for i, pp in enumerate(PREVIEWS):
        col = i % 2
        row = i // 2
        px = grid_x_start + col * (preview_w + gap)
        py = grid_y_start + row * (preview_h + gap)

        # Load and resize preview
        img = Image.open(pp).convert('RGBA')
        img_resized = img.resize((preview_w, preview_h), Image.LANCZOS)

        # --- Card/bezel background ---
        card_pad = 6
        card_x = px - card_pad
        card_y = py - card_pad
        card_w = preview_w + card_pad * 2
        card_h = preview_h + card_pad * 2

        # Outer card shadow (larger, blurred)
        shadow_layer = Image.new('RGBA', (W, H), (0, 0, 0, 0))
        sdraw = ImageDraw.Draw(shadow_layer)
        for si in range(8, 0, -1):
            alpha = 8 + si * 3
            sdraw.rounded_rectangle(
                [card_x - si, card_y - si, card_x + card_w + si, card_y + card_h + si],
                radius=corner_r + 2, fill=(0, 0, 0, alpha)
            )
        canvas = Image.alpha_composite(canvas, shadow_layer)
        draw = ImageDraw.Draw(canvas)

        # Card background (dark bezel)
        draw_rounded_rect(draw, [card_x, card_y, card_x + card_w, card_y + card_h],
                          r=corner_r + 1, fill=(20, 25, 40, 230))

        # Card border (subtle)
        draw_rounded_rect(draw, [card_x, card_y, card_x + card_w, card_y + card_h],
                          r=corner_r + 1, outline=(60, 70, 100, 120), width=1)

        # --- Screenshot with rounded corners ---
        mask = Image.new('L', (preview_w, preview_h), 0)
        mdraw = ImageDraw.Draw(mask)
        mdraw.rounded_rectangle([(0, 0), (preview_w, preview_h)], radius=corner_r, fill=255)

        # Glossy reflection on screenshot (subtle top highlight)
        gloss = Image.new('RGBA', (preview_w, preview_h), (0, 0, 0, 0))
        gldraw = ImageDraw.Draw(gloss)
        gldraw.rounded_rectangle(
            [(0, 0), (preview_w, int(preview_h * 0.3))],
            radius=corner_r, fill=(255, 255, 255, 12)
        )

        # Paste screenshot
        canvas.paste(img_resized, (px, py), mask)
        canvas.paste(gloss, (px, py), mask)

        # Screenshot border (very thin, white glow)
        draw_rounded_rect(draw, [px, py, px + preview_w, py + preview_h],
                          r=corner_r, outline=(255, 255, 255, 30), width=1)

    # ============================================================
    # 7. DESCRIPTION TEXT (Below preview grid)
    # ============================================================
    desc_x = grid_x_start
    desc_y = grid_y_start + 2 * (preview_h + gap) + 12
    desc_w = 2 * preview_w + gap  # same width as the grid

    desc_lines = [
        '小米手环上的离线词典 — 支持英语精确/前缀匹配、',
        '中文拼音输入、变形反查，约15K英文词条 + 128K中文词组',
    ]

    for li, line in enumerate(desc_lines):
        draw.text((desc_x, desc_y + li * 24), line, fill=GRAY, font=ft_reg_cn_sm)

    # ============================================================
    # 8. VERTICAL DIVIDER between title and preview areas
    # ============================================================
    divider_x = 470
    draw.line([(divider_x, 60), (divider_x, H - 60)], fill=(255, 255, 255, 8))

    # ============================================================
    # 9. BOTTOM BAR
    # ============================================================
    bar_y = H - 44

    # Gradient line (subtle highlight above bar)
    draw.line([(0, bar_y - 1), (W, bar_y - 1)], fill=(255, 255, 255, 8))
    draw.line([(0, bar_y), (W, bar_y)], fill=(255, 255, 255, 20))

    # Bottom left
    version_text = '腕上词典 v1.0.0  |  小米手环 Vela 快应用'
    draw.text((52, bar_y + 10), version_text, fill=DIM, font=ft_en_light_sm)

    # Bottom right
    github_text = '开源 github.com/pcai7296/wrist-dictionary'
    # Right-align
    gbbox = draw.textbbox((0, 0), github_text, font=ft_en_light_sm)
    gtw = gbbox[2] - gbbox[0]
    draw.text((W - 52 - gtw, bar_y + 10), github_text, fill=DIM, font=ft_en_light_sm)

    # ============================================================
    # 10. FINAL TOUCHES - vignette overlay
    # ============================================================
    vignette = Image.new('RGBA', (W, H), (0, 0, 0, 0))
    vdraw = ImageDraw.Draw(vignette)

    # Corner darkening
    for y in range(H):
        for x in range(W):
            # Distance from center
            dx_n = (x - W/2) / (W/2)
            dy_n = (y - H/2) / (H/2)
            dist = min(1.0, math.sqrt(dx_n*dx_n + dy_n*dy_n))
            if dist > 0.7:
                t = (dist - 0.7) / 0.3
                alpha = int(t * 40)
                if alpha > 0:
                    vignette.putpixel((x, y), (0, 0, 0, alpha))

    canvas = Image.alpha_composite(canvas, vignette)

    # ============================================================
    # 11. SAVE
    # ============================================================
    canvas = canvas.convert('RGB')
    canvas.save(OUT, 'PNG')
    print(f'[OK] Cover saved: {OUT} ({W}x{H})')
    print(f'   Size: {os.path.getsize(OUT) / 1024:.1f} KB')
    return OUT


if __name__ == '__main__':
    create_cover()
