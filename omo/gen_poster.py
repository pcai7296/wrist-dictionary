"""Poster v11 — 4 devices in 2 layers: S4+Redmi back, Band Pro+Band 10 front (1.5x)."""
from PIL import Image, ImageDraw, ImageFont
import os

SCREENSHOT_DIR = r'C:\Users\Administrator\.vela\sdk\screenshot'

BASE = r'J:\code\MI band\腕上词典\release_repo'
OUT = os.path.join(BASE, 'cover.png')

SHOTS = {
    's4':     os.path.join(SCREENSHOT_DIR, 'xiaomi_watch-2026-07-18-23-01-30.png'),
    'band10': os.path.join(SCREENSHOT_DIR, 'xiaomi_band_10-2026-07-18-23-05-31.png'),
    'bandpro':os.path.join(SCREENSHOT_DIR, 'xiaomi_band_pro-2026-07-18-23-01-40.png'),
    'redmi':  os.path.join(SCREENSHOT_DIR, 'redmi_watch-2026-07-18-23-00-22.png'),
}

FONT_BOLD = r'C:\Windows\Fonts\msyhbd.ttc'
FONT_REG = r'C:\Windows\Fonts\msyh.ttc'

W, H = 1800, 1200
WHITE = (255, 255, 255)
DARK = (2, 8, 19)
SKY_TOP = (112, 195, 255)
SKY_MID = (90, 175, 245)
SKY_BOT = (60, 150, 225)

DEVICE_H = 630
OVERLAP_Y = int(DEVICE_H * 0.5)


def load_font(path, size):
    try:
        return ImageFont.truetype(path, size)
    except Exception:
        return ImageFont.load_default()


def wrap_text(draw, text, font, max_width):
    if draw.textbbox((0, 0), text, font=font)[2] <= max_width:
        return [text]
    lines = []
    remaining = text
    while remaining:
        w = draw.textbbox((0, 0), remaining, font=font)[2]
        if w <= max_width:
            lines.append(remaining)
            break
        lo, hi = 1, len(remaining)
        while lo < hi:
            mid = (lo + hi + 1) // 2
            if draw.textbbox((0, 0), remaining[:mid], font=font)[2] <= max_width:
                lo = mid
            else:
                hi = mid - 1
        cut = lo
        for i in range(lo, max(lo - 12, 1) - 1, -1):
            if remaining[i - 1] in ' ,.;: ':
                cut = i
                break
        lines.append(remaining[:cut])
        remaining = remaining[cut:].lstrip()
    return lines


def fit_screenshot(src, target_w, target_h, corner_radius=0, is_circle=False):
    src_w, src_h = src.size
    src_ratio = src_w / src_h
    target_ratio = target_w / target_h
    if src_ratio > target_ratio:
        new_h = src_h
        new_w = int(src_h * target_ratio)
    else:
        new_w = src_w
        new_h = int(src_w / target_ratio)
    left = (src_w - new_w) // 2
    top = (src_h - new_h) // 2
    cropped = src.crop((left, top, left + new_w, top + new_h))
    resized = cropped.resize((target_w, target_h), Image.LANCZOS).convert('RGBA')
    mask = Image.new('L', (target_w, target_h), 0)
    md = ImageDraw.Draw(mask)
    if is_circle:
        md.ellipse([(0, 0), (target_w, target_h)], fill=255)
    elif corner_radius > 0:
        md.rounded_rectangle([(0, 0), (target_w - 1, target_h - 1)], radius=corner_radius, fill=255)
    else:
        mask = Image.new('L', (target_w, target_h), 255)
    result = Image.new('RGBA', (target_w, target_h), (0, 0, 0, 0))
    result.paste(resized, (0, 0), mask)
    return result


def render_device(skin_path, screen_box, corner_radius, is_circle, target_h, screenshot_src):
    skin = Image.open(skin_path).convert('RGBA')
    scale = target_h / skin.height
    new_w = int(skin.width * scale)
    new_h = target_h
    device = skin.resize((new_w, new_h), Image.LANCZOS)
    sx1 = int(screen_box[0] * scale)
    sy1 = int(screen_box[1] * scale)
    sx2 = int(screen_box[2] * scale)
    sy2 = int(screen_box[3] * scale)
    scr_w = sx2 - sx1
    scr_h = sy2 - sy1
    screen_content = fit_screenshot(screenshot_src, scr_w, scr_h, corner_radius, is_circle)
    device.paste(screen_content, (sx1, sy1), screen_content)
    pad = 40
    shadow = Image.new('RGBA', (new_w + pad, new_h + pad), (0, 0, 0, 0))
    sd = ImageDraw.Draw(shadow)
    for s in range(20, 0, -1):
        sd.rounded_rectangle([s, s, new_w + pad - s, new_h + pad - s],
                             radius=25, fill=(0, 0, 0, 2 + s * 2))
    return device, shadow, new_w, new_h


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

    # White glow
    glow = Image.new('RGBA', (W, H), (0, 0, 0, 0))
    gdraw = ImageDraw.Draw(glow)
    cx, cy = int(W * 0.3), H // 2
    for i in range(40, 0, -1):
        a = max(0, 12 - i // 4)
        r = 240 + i * 8
        gdraw.ellipse([cx - r, cy - r, cx + r, cy + r],
                      fill=(255, 255, 255, a))
    canvas = Image.alpha_composite(canvas.convert('RGBA'), glow).convert('RGB')
    draw = ImageDraw.Draw(canvas)

    # Device configs: (name, skin_path, screen_box(x1,y1,x2,y2), corner_radius, is_circle, shot_key)
    S4 = ('s4', r'C:\Users\Administrator\.vela\sdk\skins\builtin\xiaomi_s4\background.png',
          (65, 253, 531, 719), 233, True, 's4')
    BAND_PRO = ('band_pro', r'C:\Users\Administrator\.vela\sdk\skins\builtin\xiaomi_band_pro\background.png',
                (44, 186, 380, 666), 40, False, 'bandpro')
    BAND_10 = ('band_10', r'C:\Users\Administrator\.vela\sdk\skins\builtin\xiaomi_band_10\background_l.png',
               (31, 166, 242, 683), 104, False, 'band10')
    REDMI = ('redmi', r'C:\Users\Administrator\.vela\sdk\skins\builtin\redmi_watch\background.png',
             (47, 182, 479, 696), 80, False, 'redmi')

    # Load all screenshots
    shots = {}
    for key, path in SHOTS.items():
        shots[key] = Image.open(path).convert('RGBA') if os.path.exists(path) \
            else Image.new('RGBA', (1, 1), DARK)

    def render(cfg):
        name, skin_path, screen_box, cr, is_circle, shot_key = cfg
        return render_device(skin_path, screen_box, cr, is_circle, DEVICE_H, shots[shot_key])

    s4_img, s4_sh, s4_w, _ = render(S4)
    bp_img, bp_sh, bp_w, _ = render(BAND_PRO)
    b10_img, b10_sh, b10_w, _ = render(BAND_10)
    rm_img, rm_sh, rm_w, _ = render(REDMI)

    # Layout: back layer (S4 + Redmi), front layer (Band Pro + Band 10)
    cluster_h = DEVICE_H * 3 // 2
    back_y = (H - cluster_h) // 2
    front_y = back_y + OVERLAP_Y

    gap_between_back = 15
    s4_x = 80
    rm_x = s4_x + s4_w + gap_between_back

    bp_x = s4_x + int(s4_w * 0.3)
    b10_x = rm_x + int(rm_w * 0.4)

    # Center cluster in left zone (0-990)
    left_zone = 990
    xs = [s4_x, rm_x, bp_x, b10_x]
    ws = [s4_w, rm_w, bp_w, b10_w]
    rightmost = max(x + w for x, w in zip(xs, ws))
    leftmost = min(xs)
    shift_x = int(left_zone / 2 - (leftmost + rightmost) / 2)
    s4_x += shift_x
    rm_x += shift_x
    bp_x += shift_x
    b10_x += shift_x

    # Composite: back layer first, then front
    canvas_rgba = canvas.convert('RGBA')

    def paste_dev(img, shad, x, y):
        canvas_rgba.paste(shad, (x - 20, y - 20), shad)
        canvas_rgba.paste(img, (x, y), img)

    paste_dev(s4_img, s4_sh, s4_x, back_y)
    paste_dev(rm_img, rm_sh, rm_x, back_y)
    paste_dev(bp_img, bp_sh, bp_x, front_y)
    paste_dev(b10_img, b10_sh, b10_x, front_y)

    canvas = canvas_rgba.convert('RGB')
    draw = ImageDraw.Draw(canvas)

    # Right side text
    tx0 = 960
    ft_title = load_font(FONT_BOLD, 210)
    ft_sub = load_font(FONT_BOLD, 72)
    ft_feat = load_font(FONT_BOLD, 78)
    ft_desc = load_font(FONT_REG, 52)

    title_y = 20
    for s in range(8, 0, -1):
        a = max(8, 40 - s * 5)
        draw.text((tx0 + s * 4, title_y + s * 4),
                  '腕上词典', fill=(0, 40, 120, a), font=ft_title)
    draw.text((tx0, title_y), '腕上词典', fill=WHITE, font=ft_title)
    tb = draw.textbbox((0, 0), '腕上词典', font=ft_title)
    title_h = tb[3] - tb[1]
    title_bottom = title_y + title_h

    sub_y = title_bottom + 40
    sub_text = '离线英汉词典 | 抬手即查'
    draw.text((tx0, sub_y), sub_text, fill=(220, 238, 255), font=ft_sub)
    sb = draw.textbbox((0, 0), sub_text, font=ft_sub)
    sub_h = sb[3] - sb[1]
    sub_w = sb[2] - sb[0]
    avail_w = W - tx0
    if sub_w > avail_w:
        print(f'WARNING: subtitle {sub_w}px > avail {avail_w}px')
    print(f'Subtitle: w={sub_w} avail={avail_w}')

    features = [
        ('中英查词', '1.5万词库，离线可用'),
        ('变形反查', '输入 ran 找 run'),
        ('模糊搜索', '容错纠错，拼写不怕错'),
        ('收藏历史', '一键收藏，随时复习'),
        ('多屏适配', '适配 S4·Pro·10·Redmi'),
    ]
    feat_y = sub_y + sub_h + 25
    for f_title, f_desc in features:
        ftb = draw.textbbox((0, 0), f_title, font=ft_feat)
        f_title_h = ftb[3] - ftb[1]
        desc_lines = wrap_text(draw, f_desc, ft_desc, avail_w)
        draw.text((tx0, feat_y), f_title, fill=WHITE, font=ft_feat)
        desc_y = feat_y + f_title_h + 4
        for dl in desc_lines:
            draw.text((tx0, desc_y), dl, fill=(200, 225, 250), font=ft_desc)
            desc_y += ft_desc.size + 6
        n_lines = len(desc_lines)
        total_desc_h = n_lines * ft_desc.size + (n_lines - 1) * 4
        feat_y += f_title_h + 3 + total_desc_h + 10

    print(f'Back={back_y} Front={front_y}')
    print(f'S4=({s4_x},{back_y}) BP=({bp_x},{front_y}) B10=({b10_x},{front_y}) RM=({rm_x},{back_y})')
    def overlap_pct(a_x, a_w, b_x, b_w):
        overlap = max(0, min(a_x + a_w, b_x + b_w) - max(a_x, b_x))
        return overlap / a_w * 100 if a_w else 0
    print(f'Overlap BP/S4: {overlap_pct(s4_x, s4_w, bp_x, bp_w):.0f}%  B10/RM: {overlap_pct(rm_x, rm_w, b10_x, b10_w):.0f}%')

    canvas.save(OUT)
    print(f'[OK] Poster v11: {OUT}')


if __name__ == '__main__':
    create_cover()
