"""Poster v9 — precise reference proportions from PIL measurement."""
from PIL import Image, ImageDraw, ImageFont
import os

BASE = r'J:\code\MI band\腕上词典\release_repo'
OUT = os.path.join(BASE, 'cover.png')
HOME = os.path.join(BASE, 'preview', '01_home.png')
SKIN = r'C:\Users\Administrator\.vela\sdk\skins\builtin\xiaomi_band_10\background_l.png'

FONT_BOLD = r'C:\Windows\Fonts\msyhbd.ttc'
FONT_REG = r'C:\Windows\Fonts\msyh.ttc'

W, H = 1800, 1200

WHITE = (255, 255, 255)
SKY_TOP = (112, 195, 255)
SKY_MID = (90, 175, 245)
SKY_BOT = (60, 150, 225)
DEEP = (0, 55, 150)

SKIN_SCREEN = (31, 166, 242, 683)

REDMI_SKIN = r'C:\Users\Administrator\.vela\sdk\skins\builtin\redmi_watch\background.png'
REDMI_SCREEN = (47, 182, 432, 514)  # (x, y, w, h) in the 560×870 skin
REDMI_CR = 80

def load_font(path, size):
    try:
        return ImageFont.truetype(path, size)
    except:
        return ImageFont.load_default()


def wrap_text(draw, text, font, max_width):
    """Break text into lines fitting max_width. Prefers breaks at spaces/punctuation."""
    if draw.textbbox((0, 0), text, font=font)[2] <= max_width:
        return [text]

    lines = []
    remaining = text
    while remaining:
        w = draw.textbbox((0, 0), remaining, font=font)[2]
        if w <= max_width:
            lines.append(remaining)
            break

        # Binary search: longest prefix that fits
        lo, hi = 1, len(remaining)
        while lo < hi:
            mid = (lo + hi + 1) // 2
            if draw.textbbox((0, 0), remaining[:mid], font=font)[2] <= max_width:
                lo = mid
            else:
                hi = mid - 1

        # Walk backward to find natural break point (space / punctuation)
        cut = lo
        for i in range(lo, max(lo - 12, 1) - 1, -1):
            if remaining[i - 1] in ' ，、；：. ':
                cut = i
                break

        lines.append(remaining[:cut])
        remaining = remaining[cut:].lstrip()

    return lines


def create_cover():
    canvas = Image.new('RGB', (W, H))
    draw = ImageDraw.Draw(canvas)

    # Sky-blue gradient
    for y in range(H):
        t = y / H
        if t < 0.5:
            t2 = t * 2
            r = int(SKY_TOP[0] + (SKY_MID[0] - SKY_TOP[0]) * t2)
            g = int(SKY_TOP[1] + (SKY_MID[1] - SKY_TOP[1]) * t2)
            b = int(SKY_TOP[2] + (SKY_MID[2] - SKY_TOP[2]) * t2)
        else:
            t2 = (t - 0.5) * 2
            r = int(SKY_MID[0] + (SKY_BOT[0] - SKY_MID[0]) * t2)
            g = int(SKY_MID[1] + (SKY_BOT[1] - SKY_MID[1]) * t2)
            b = int(SKY_MID[2] + (SKY_BOT[2] - SKY_MID[2]) * t2)
        draw.line([(0, y), (W, y)], fill=(r, g, b))

    # White glow behind device
    glow = Image.new('RGBA', (W, H), (0, 0, 0, 0))
    gdraw = ImageDraw.Draw(glow)
    cx, cy = int(W * 0.16), H // 2
    for i in range(35, 0, -1):
        a = max(0, 10 - i // 4)
        r = 180 + i * 8
        gdraw.ellipse([cx - r, cy - r, cx + r, cy + r],
                      fill=(255, 255, 255, a))
    canvas = Image.alpha_composite(canvas.convert('RGBA'), glow).convert('RGB')
    draw = ImageDraw.Draw(canvas)

    # ===== DEVICE =====
    skin = Image.open(SKIN).convert('RGBA')
    home_img = Image.open(HOME).convert('RGBA') if os.path.exists(HOME) \
        else Image.new('RGBA', (212, 520), (10, 15, 35))

    device_target_h = int(H * 0.76)
    scale = device_target_h / skin.height
    skin_w = int(skin.width * scale)
    skin_h = device_target_h

    skin_resized = skin.resize((skin_w, skin_h), Image.LANCZOS)
    sx1 = int(SKIN_SCREEN[0] * scale)
    sy1 = int(SKIN_SCREEN[1] * scale)
    sx2 = int(SKIN_SCREEN[2] * scale)
    sy2 = int(SKIN_SCREEN[3] * scale)
    home_scaled = home_img.resize((sx2 - sx1, sy2 - sy1), Image.LANCZOS)
    skin_resized.paste(home_scaled, (sx1, sy1), home_scaled)

    shadow = Image.new('RGBA', (skin_w + 60, skin_h + 60), (0, 0, 0, 0))
    sh_draw = ImageDraw.Draw(shadow)
    for s in range(20, 0, -1):
        sh_draw.rounded_rectangle([s, s, skin_w + 60 - s, skin_h + 60 - s],
                                  radius=40, fill=(0, 0, 0, 3 + s * 2))
    canvas.paste(shadow, (int(W * 0.05) - 30, (H - skin_h) // 2 - 30), shadow)
    canvas.paste(skin_resized, (int(W * 0.05), (H - skin_h) // 2), skin_resized)

    # ===== RIGHT SIDE — dynamic spacing based on measured text =====
    tx0 = int(W * 0.5)

    ft_title = load_font(FONT_BOLD, 210)
    ft_sub = load_font(FONT_BOLD, 80)   # 80px: fits within right-half (900px) after moving tx0 to center
    ft_feat = load_font(FONT_BOLD, 80)
    ft_desc = load_font(FONT_REG, 52)

    # Title
    title_y = 20
    for s in range(8, 0, -1):
        a = max(8, 40 - s * 5)
        draw.text((tx0 + s * 4, title_y + s * 4),
                  '腕上词典', fill=(0, 40, 120, a), font=ft_title)
    draw.text((tx0, title_y), '腕上词典', fill=WHITE, font=ft_title)

    tb = draw.textbbox((0, 0), '腕上词典', font=ft_title)
    title_h = tb[3] - tb[1]
    title_bottom = title_y + title_h

    # Subtitle — measured to ensure width fits within canvas
    sub_y = title_bottom + 40
    sub_text = '离线英汉词典 | 抬手即查'
    draw.text((tx0, sub_y), sub_text, fill=(220, 238, 255), font=ft_sub)

    sb = draw.textbbox((0, 0), sub_text, font=ft_sub)
    sub_h = sb[3] - sb[1]
    sub_w = sb[2] - sb[0]
    avail_w = W - tx0
    if sub_w > avail_w:
        print(f'  WARNING: subtitle width {sub_w}px exceeds available {avail_w}px — truncation risk!')
    print(f'  Subtitle: ft=80px, w={sub_w}px, h={sub_h}px, avail={avail_w}px')

    # Feature items — rewritten from actual app features
    features = [
        ('中英查词', '1.5万英文词 + 12万中文词组'),
        ('变形反查', '输入 ran 找 run，输入 better 找 good'),
        ('模糊搜索', '拼写错误自动容错，最多 2 字符差异'),
        ('收藏历史', '生词一键收藏，搜索自动记录'),
    ]

    feat_y = sub_y + sub_h + 25

    for f_title, f_desc in features:
        ftb = draw.textbbox((0, 0), f_title, font=ft_feat)
        f_title_h = ftb[3] - ftb[1]

        # Wrap description to available width
        desc_lines = wrap_text(draw, f_desc, ft_desc, avail_w)

        draw.text((tx0, feat_y), f_title, fill=WHITE, font=ft_feat)

        desc_y = feat_y + f_title_h + 4
        for dl in desc_lines:
            draw.text((tx0, desc_y), dl, fill=(200, 225, 250), font=ft_desc)
            desc_y += ft_desc.size + 6

        n_lines = len(desc_lines)
        total_desc_h = n_lines * ft_desc.size + (n_lines - 1) * 4
        feat_y += f_title_h + 3 + total_desc_h + 10

    feat_end = feat_y
    print(f'  Features range: {sub_y + sub_h + 40} to {feat_end} ({feat_end - (sub_y + sub_h + 40)}px)')
    print(f'  Content block: {title_y} to {feat_end} ({feat_end - title_y}px)')
    print(f'  Bottom margin: {H - feat_end}px')
    if H - feat_end < 30:
        print('  WARNING: very tight bottom margin!')

    # ===== REDMI WATCH (top layer, skin + screenshot, bottom-aligned with band) =====
    REDMI_SHOT = os.path.join(BASE, 'review', '5_home.png')
    redmi_bg = Image.open(REDMI_SKIN).convert('RGBA')

    # Scale skin: height matches band (912px) so bottom-align is natural
    r_scale = skin_h / redmi_bg.height  # use same height as Mi Band 10
    r_w = int(redmi_bg.width * r_scale)
    r_h = skin_h

    # Bottom-align with Mi Band 10
    band_bottom = (H - skin_h) // 2 + skin_h  # 1056
    r_x = 280
    r_y = band_bottom - r_h

    redmi_resized = redmi_bg.resize((r_w, r_h), Image.LANCZOS)

    # Paste screenshot onto screen area (scaled to match)
    r_sx = int(REDMI_SCREEN[0] * r_scale)
    r_sy = int(REDMI_SCREEN[1] * r_scale)
    r_sw = int(REDMI_SCREEN[2] * r_scale)
    r_sh = int(REDMI_SCREEN[3] * r_scale)
    redmi_shot = Image.open(REDMI_SHOT).convert('RGBA')
    redmi_shot_scaled = redmi_shot.resize((r_sw, r_sh), Image.LANCZOS)

    # Rounded-corner mask
    screen_mask = Image.new('L', (r_sw, r_sh), 0)
    sm_draw = ImageDraw.Draw(screen_mask)
    r_cr = int(REDMI_CR * r_scale)
    sm_draw.rounded_rectangle([(0, 0), (r_sw, r_sh)], radius=r_cr, fill=255)
    redmi_resized.paste(redmi_shot_scaled, (r_sx, r_sy), screen_mask)

    # Shadow
    r_shadow = Image.new('RGBA', (r_w + 40, r_h + 40), (0, 0, 0, 0))
    rs_draw = ImageDraw.Draw(r_shadow)
    for s in range(15, 0, -1):
        rs_draw.rounded_rectangle([s, s, r_w + 40 - s, r_h + 40 - s],
                                  radius=20, fill=(0, 0, 0, 2 + s * 2))
    canvas.paste(r_shadow, (r_x - 20, r_y - 20), r_shadow)
    canvas.paste(redmi_resized, (r_x, r_y), redmi_resized)

    print(f'  Redmi Watch: at ({r_x},{r_y}), scaled {r_w}x{r_h}, bottom={r_y + r_h}')

    canvas.save(OUT)
    print(f'[OK] Poster v9: {OUT}')
    print(f'  Title: ft=210px, rendered_h={title_h}px ({title_h/H*100:.1f}%)')
    print(f'  Subtitle: ft=80px')

if __name__ == '__main__':
    create_cover()
