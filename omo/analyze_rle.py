"""Analyze whether the compact-v3 zh index benefits from run-length encoding.

compact-v3 stores delta IDs as URL-safe Base64-wrapped ULEB128 bytes.  RLE
analysis must therefore inspect decoded deltas rather than treating the
encoded text as comma-separated base36 tokens.
"""

import sys
from collections import Counter
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.generate_watch_dict import decode_delta_ids


ZH_DIR = ROOT / "src" / "common" / "dict" / "zh_index"


def main() -> None:
    total_ids = 0
    total_deltas = 0
    runs: list[tuple[int, int]] = []

    for path in sorted(ZH_DIR.glob("zh_*.txt")):
        for line_number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
            parts = line.split("\t", 1)
            if len(parts) != 2:
                continue
            ids = decode_delta_ids(parts[1])
            if not ids:
                raise ValueError(f"invalid compact-v3 payload: {path}:{line_number}")
            total_ids += len(ids)
            deltas = [ids[0], *[current - previous for previous, current in zip(ids, ids[1:])]]
            total_deltas += len(deltas)
            current_run = 1
            for previous, current in zip(deltas, deltas[1:]):
                if current == previous:
                    current_run += 1
                else:
                    if current_run > 1:
                        runs.append((previous, current_run))
                    current_run = 1
            if current_run > 1:
                runs.append((deltas[-1], current_run))

    print("Encoding: compact-v3 Base64URL + ULEB128 delta IDs")
    print(f"Total decoded IDs: {total_ids:,}")
    print(f"Total decoded deltas: {total_deltas:,}")
    if not runs:
        print("RLE candidate runs: 0")
        print("RLE is not applicable to the current data")
        return

    repeated = sum(length for _, length in runs)
    print(f"RLE candidate runs: {len(runs):,}")
    print(f"Deltas in runs >1: {repeated:,} ({repeated / total_deltas * 100:.1f}%)")
    print("RLE is not part of compact-v3; this is analysis only")
    print(f"Max run: {max(length for _, length in runs)}")
    for length, count in sorted(Counter(length for _, length in runs).items()):
        print(f"  Run length {length}: {count} runs")


if __name__ == "__main__":
    main()
