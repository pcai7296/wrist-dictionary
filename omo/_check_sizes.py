import os
# Check english_suggestions and InputMethod sizes
f1 = r'J:\code\MI band\腕上词典\src\common\english_suggestions.js'
f2 = r'J:\code\MI band\腕上词典\src\components\InputMethod'
for root, dirs, files in os.walk(f2):
    for f in files:
        fp = os.path.join(root, f)
        sz = os.path.getsize(fp)
        rel = os.path.relpath(fp, f2)
        print(f'  {rel}: {sz:,} bytes ({sz/1024:.1f} KB)')

print()
print(f'english_suggestions.js: {os.path.getsize(f1):,} bytes')
