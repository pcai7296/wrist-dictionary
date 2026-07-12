"""Cover 16:9 — 单截图右侧展示，左侧极简文案"""

from PIL import Image, ImageDraw, ImageFont
import os

WIDTH, HEIGHT = 1200, 675
BASE = r'J:\code\MI band\腕上词典\release_repo'
OUTPUT_FILE = os.path.join(BASE, 'cover.png')

FONT_BOLD = r'C:\Windows\Fonts\msyhbd.ttc'
FONT_REG = r'C:\Windows\Fonts\msyh.ttc'

BG_START = (10, 15, 35)
BG_END = (5, 10, 25)
ACCENT_BLUE = (0, 122, 255)
TEXT_WHITE = (255, 255, 255)
TEXT_GRAY = (150, 160, 180)
CARD_BG = (20, 25, 45)

def load_font(path, size):
    try: return ImageFont.truetype(path, size)
    except: return ImageFont.load_default()


def create_cover():
    # ===== 渐变背景 =====
    base_img = Image.new('RGB', (WIDTH, HEIGHT))
    draw = ImageDraw.Draw(base_img)
    for y in range(HEIGHT):
        r = int(BG_START[0] + (BG_END[0] - BG_START[0]) * y / HEIGHT)
        g = int(BG_START[1] + (BG_END[1] - BG_START[1]) * y / HEIGHT)
        b = int(BG_START[2] + (BG_END[2] - BG_START[2]) * y / HEIGHT)
        draw.line([(0, y), (WIDTH, y)], fill=(r, g, b))

    # ===== 光晕（在半透明 layer 上画再合成，避免 RGB alpha 报错） =====
    glow = Image.new('RGBA', (WIDTH, HEIGHT), (0, 0, 0, 0))
    gdraw = ImageDraw.Draw(glow)
    gdraw.ellipse(
        [(WIDTH // 2 - 300, HEIGHT // 2 - 200), (WIDTH // 2 + 300, HEIGHT // 2 + 200)],
        fill=(50, 100, 200, 30))
    base_img = Image.alpha_composite(base_img.convert('RGBA'), glow).convert('RGB')
    draw = ImageDraw.Draw(base_img)

    # ===== 字体 =====
    title_font = load_font(FONT_BOLD, 56)
    dev_font = load_font(FONT_REG, 20)
    badge_font = load_font(FONT_BOLD, 24)
    label_font = load_font(FONT_REG, 18)

    # ===== 左侧文案 =====
    # 主标题（居中于左半区）
    title_text = "英汉词典"
    bbox = draw.textbbox((0, 0), title_text, font=title_font)
    title_w = bbox[2] - bbox[0]
    title_x = (WIDTH // 2 - 280) - title_w // 2
    draw.text((title_x, 100), title_text, fill=TEXT_WHITE, font=title_font)

    # 副标题
    dev_text = "AstrolChase Develop"
    draw.text((title_x, 130), dev_text, fill=TEXT_GRAY, font=dev_font)

    # 核心标签
    badge_text = "完全免费"
    badge_bbox = draw.textbbox((0, 0), badge_text, font=badge_font)
    badge_w = badge_bbox[2] - badge_bbox[0] + 40
    badge_h = 50
    bx = (WIDTH // 2 - 280) - badge_w // 2
    by = 170
    draw.rounded_rectangle([(bx, by), (bx + badge_w, by + badge_h)], radius=25, fill="black")
    draw.text((bx + 20, by + 12), badge_text, fill=TEXT_WHITE, font=badge_font)

    # ===== 右侧截图 =====
    # 使用第一张预览图
    img_path = os.path.join(BASE, 'preview', '01_home.png')
    content_img = Image.open(img_path).convert('RGBA')
    target_h = HEIGHT - 100
    wpercent = target_h / float(content_img.size[1])
    target_w = int(float(content_img.size[0]) * wpercent)
    content_img = content_img.resize((target_w, target_h), Image.LANCZOS)

    px = WIDTH // 2 - 80
    py = (HEIGHT - content_img.height) // 2

    # 阴影
    shadow = Image.new('RGBA', (content_img.width + 20, content_img.height + 20), (0, 0, 0, 100))
    base_img.paste(shadow, (px - 10, py - 10), shadow)
    base_img.paste(content_img, (px, py), content_img)

    # ===== 保存 =====
    base_img.save(OUTPUT_FILE)
    print(f'[OK] Cover saved: {OUTPUT_FILE}')


if __name__ == '__main__':
    create_cover()
