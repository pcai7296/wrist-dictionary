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

def load_font(path, size):
    try:
        return ImageFont.truetype(path, size)
    except:
        return ImageFont.load_default()

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
    tx0 = int(W * 0.34)

    ft_title = load_font(FONT_BOLD, 210)
    ft_sub = load_font(FONT_BOLD, 95)   # 95px: width~1040 < 1188 available — safe from truncation
    ft_feat = load_font(FONT_BOLD, 90)
    ft_desc = load_font(FONT_REG, 60)

    # Title
    title_y = 35
    for s in range(8, 0, -1):
        a = max(8, 40 - s * 5)
        draw.text((tx0 + s * 4, title_y + s * 4),
                  '腕上词典', fill=(0, 40, 120, a), font=ft_title)
    draw.text((tx0, title_y), '腕上词典', fill=WHITE, font=ft_title)

    tb = draw.textbbox((0, 0), '腕上词典', font=ft_title)
    title_h = tb[3] - tb[1]
    title_bottom = title_y + title_h

    # Subtitle — measured to ensure width fits within canvas
    sub_y = title_bottom + 55
    sub_text = '离线英汉词典 | 抬手即查'
    draw.text((tx0, sub_y), sub_text, fill=(220, 238, 255), font=ft_sub)

    sb = draw.textbbox((0, 0), sub_text, font=ft_sub)
    sub_h = sb[3] - sb[1]
    sub_w = sb[2] - sb[0]
    avail_w = W - tx0
    if sub_w > avail_w:
        print(f'  WARNING: subtitle width {sub_w}px exceeds available {avail_w}px — truncation risk!')
    print(f'  Subtitle: ft=95px, w={sub_w}px, h={sub_h}px, avail={avail_w}px')

    # Feature items — rewritten from actual app features
    features = [
        ('中英查词', '1.5万英文词 + 12万中文词组'),
        ('变形反查', '输入 ran 找 run，输入 better 找 good'),
        ('模糊搜索', '拼写错误自动容错，最多 2 字符差异'),
        ('收藏历史', '生词一键收藏，搜索自动记录'),
    ]

    feat_y = sub_y + sub_h + 40

    for f_title, f_desc in features:
        # Measure this feature's actual title height
        ftb = draw.textbbox((0, 0), f_title, font=ft_feat)
        f_title_h = ftb[3] - ftb[1]

        fdb = draw.textbbox((0, 0), f_desc, font=ft_desc)
        f_desc_h = fdb[3] - fdb[1]

        # Desc starts AFTER the title ends (not inside it)
        desc_y = feat_y + f_title_h + 4

        draw.text((tx0, feat_y), f_title, fill=WHITE, font=ft_feat)
        draw.text((tx0, desc_y), f_desc, fill=(200, 225, 250), font=ft_desc)

        # Line height = title + 4px gap + desc + 12px inter-feature padding
        feat_y += f_title_h + 4 + f_desc_h + 12

    feat_end = feat_y
    print(f'  Features range: {sub_y + sub_h + 40} to {feat_end} ({feat_end - (sub_y + sub_h + 40)}px)')
    print(f'  Content block: {title_y} to {feat_end} ({feat_end - title_y}px)')
    print(f'  Bottom margin: {H - feat_end}px')
    if H - feat_end < 30:
        print('  WARNING: very tight bottom margin!')

    canvas.save(OUT)
    print(f'[OK] Poster v9: {OUT}')
    print(f'  Title: ft=210px, rendered_h={title_h}px ({title_h/H*100:.1f}%)')
    print(f'  Subtitle: ft=95px')

if __name__ == '__main__':
    create_cover()
