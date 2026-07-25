"""Check compact-v4 dictionary sizes and acceptance gates."""

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DICT_DIR = ROOT / "src" / "common" / "dict"
INPUT_METHOD_DIR = ROOT / "src" / "components" / "InputMethod"

EXPECTED = {
    "cn_index": (96, 40 * 1024),
    "zh_index": (64, None),
    "inflect": (26, 28 * 1024),
    "inflect_reverse": (26, 32 * 1024),
}

MAX_SCAN_ROWS = {
    "inflect": 3_000,
    "inflect_reverse": 1_400,
}


def files_in(directory: Path) -> list[Path]:
    return sorted(path for path in directory.iterdir() if path.suffix in (".txt", ".bin") and path.is_file())


def main() -> None:
    meta = json.loads((DICT_DIR / "meta.json").read_text(encoding="utf-8"))
    if meta.get("schema") != "compact-v4":
        raise SystemExit(f"schema gate failed: {meta.get('schema')!r}")

    total = 0
    print("compact-v4 dictionary size report")
    for name, (expected_count, max_bytes) in EXPECTED.items():
        paths = files_in(DICT_DIR / name)
        size = sum(path.stat().st_size for path in paths)
        largest = max((path.stat().st_size for path in paths), default=0)
        total += size
        print(f"{name}: {len(paths)} files, {size:,} bytes, max {largest:,} bytes")
        if len(paths) != expected_count:
            raise SystemExit(f"file-count gate failed: {name}={len(paths)}, expected {expected_count}")
        if max_bytes is not None and largest > max_bytes:
            raise SystemExit(f"max-file gate failed: {name}={largest}, limit {max_bytes}")
        if name in MAX_SCAN_ROWS:
            max_rows = max((len(path.read_text(encoding="utf-8").splitlines()) for path in paths), default=0)
            print(f"{name} max scan rows: {max_rows:,}")
            if max_rows > MAX_SCAN_ROWS[name]:
                raise SystemExit(
                    f"scan-row gate failed: {name}={max_rows}, limit {MAX_SCAN_ROWS[name]}"
                )

    for name in ("words", "entries"):
        paths = files_in(DICT_DIR / name)
        size = sum(path.stat().st_size for path in paths)
        total += size
        largest = max((path.stat().st_size for path in paths), default=0)
        print(f"{name}: {len(paths)} files, {size:,} bytes, max {largest:,} bytes")

    meta_size = (DICT_DIR / "meta.json").stat().st_size
    total += meta_size
    print(f"meta.json: {meta_size:,} bytes")
    print(f"dictionary total: {total:,} bytes")

    if total > 3_800_000:
        raise SystemExit(f"total-size gate failed: {total:,} > 3,800,000")

    word_count = sum(
        1
        for path in files_in(DICT_DIR / "words")
        for line in path.read_text(encoding="utf-8").splitlines()
        if line
    )
    if word_count != 14_942:
        raise SystemExit(f"word-count gate failed: {word_count}")
    word_bytes = sum(path.stat().st_size for path in files_in(DICT_DIR / "words"))
    print(f"Compact word index: {word_count:,} entries, {word_bytes:,} bytes")

    for path in sorted(item for item in INPUT_METHOD_DIR.rglob("*") if item.is_file()):
        size = path.stat().st_size
        relative = path.relative_to(INPUT_METHOD_DIR)
        print(f"  {relative}: {size:,} bytes ({size / 1024:.1f} KB)")


if __name__ == "__main__":
    main()
