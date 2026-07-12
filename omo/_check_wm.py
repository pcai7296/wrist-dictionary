"""Check bottom-right for watermark text more carefully"""
from PIL import Image

img = Image.open(r"C:\Users\Administrator\Downloads\17cd6d44d02f4.png").convert("RGB")
pixels = img.load()
w, h = img.size

# Check the bottom-right corner more carefully
# Area: x=800-1020, y=940-1010
print("=== Pixel values in bottom-right area ===")
for y in range(h-80, h-10):
    for x in range(w-190, w-20):
        r, g, b = pixels[x, y]
        # Check if pixel is significantly different from its neighbors
        # (text edge detection)
        if abs(r - g) + abs(g - b) > 15:  # colored pixel on white bg
            print(f"({x},{y}): RGB({r},{g},{b}) - colored/text")

# Also look for gray text (gray on white bg)
print("\n=== Gray pixels (possible text) ===")
for y in range(h-80, h-10):
    for x in range(w-190, w-20):
        r, g, b = pixels[x, y]
        bright = (r + g + b) / 3
        if 80 < bright < 200:  # gray, not pure white or pure black
            print(f"({x},{y}): RGB({r},{g},{b}) - gray")
