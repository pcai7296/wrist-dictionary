"""Report compact dictionary index and input-method asset sizes."""

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
WORD_DIR = ROOT / "src" / "common" / "dict" / "words"
INPUT_METHOD_DIR = ROOT / "src" / "components" / "InputMethod"


word_files = sorted(WORD_DIR.glob("word_*.txt"))
word_entries = sum(
    1
    for path in word_files
    for line in path.read_text(encoding="utf-8").splitlines()
    if line
)
word_bytes = sum(path.stat().st_size for path in word_files)
print(f"Compact word index: {word_entries:,} entries, {word_bytes:,} bytes")

for path in sorted(item for item in INPUT_METHOD_DIR.rglob("*") if item.is_file()):
    size = path.stat().st_size
    relative = path.relative_to(INPUT_METHOD_DIR)
    print(f"  {relative}: {size:,} bytes ({size / 1024:.1f} KB)")
