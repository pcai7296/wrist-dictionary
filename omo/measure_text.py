"""Measure actual rendered text sizes."""
from PIL import ImageFont

FONT_BOLD = r'C:\Windows\Fonts\msyhbd.ttc'
FONT_REG = r'C:\Windows\Fonts\msyh.ttc'

def measure(font_path, size, text):
    f = ImageFont.truetype(font_path, size)
    b = f.getbbox(text)
    print(f'{size}px "{text}": box=({b[0]},{b[1]},{b[2]},{b[3]}) w={b[2]-b[0]}px h={b[3]-b[1]}px')

print('=== Subtitle options ===')
for s in [130, 110, 100, 90]:
    measure(FONT_BOLD, s, '离线英汉词典 | 抬手即查')

print()
print('=== Feature title 90px ===')
for t in ['英文查词', '历史记录', '关于页面', '赞助支持']:
    measure(FONT_BOLD, 90, t)

print()
print('=== Feature desc 60px ===')
for d in ['输入单词，显示释义、音标与例句', '自动保存，方便随时回顾复习', '版本信息、开源许可与联系方式', '扫码赞助，支持持续开发与维护']:
    measure(FONT_REG, 60, d)

print()
print('=== Title 210px ===')
measure(FONT_BOLD, 210, '腕上词典')
