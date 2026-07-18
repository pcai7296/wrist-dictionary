# /// script
# dependencies = []
# ///
"""Analyze how many English words match each prefix length of 1-10 letters.

Reads the compact word index, builds a prefix trie, counts leaf descendants
per depth, and prints distribution stats.
"""

from pathlib import Path


DICT_DIR = Path(__file__).resolve().parents[1] / "src" / "common" / "dict"


def read_words() -> list[str]:
    """Read every English word from the compact index."""
    words: list[str] = []
    for path in sorted(DICT_DIR.glob("words/word_*.txt")):
        prev = ""
        for line in path.read_text("utf-8").splitlines():
            if not line:
                continue
            parts = line.split("\t")
            if not parts:
                continue
            raw = parts[0]
            # front-code decode first char = prefix len
            prefix_len = int(raw[0], 36) if raw and raw[0] in "0123456789abcdefghijklmnopqrstuvwxyz" else 0
            word = prev[:prefix_len] + raw[1:]
            words.append(word.lower().strip())
            prev = word
    return words


def analyze(words: list[str]) -> None:
    """Print result count distribution for prefix lengths 1-10."""
    # Build prefix → count map
    counts: dict[int, dict[str, int]] = {n: {} for n in range(1, 11)}
    for word in words:
        for n in range(1, min(11, len(word) + 1)):
            prefix = word[:n]
            counts[n][prefix] = counts[n].get(prefix, 0) + 1

    total_words = len(words)

    print(f"Total English words: {total_words}")
    print()

    for n in range(1, 11):
        prefix_counts = list(counts[n].values())
        if not prefix_counts:
            print(f"  {n} chars: no prefixes found")
            continue

        total = len(prefix_counts)
        avg = sum(prefix_counts) / total
        med = sorted(prefix_counts)[total // 2]
        mx = max(prefix_counts)
        mn = min(prefix_counts)

        # buckets
        bucket_1_5 = sum(1 for c in prefix_counts if c <= 5)
        bucket_6_20 = sum(1 for c in prefix_counts if 5 < c <= 20)
        bucket_21_50 = sum(1 for c in prefix_counts if 20 < c <= 50)
        bucket_51plus = sum(1 for c in prefix_counts if c > 50)

        print(f"--- {n}-letter prefixes ---")
        print(f"  unique prefixes: {total}")
        print(f"  avg results:     {avg:.1f}")
        print(f"  median results:  {med}")
        print(f"  max results:     {mx}")
        print(f"  min results:     {mn}")
        print(f"  distribution:")
        print(f"    1-5:    {bucket_1_5:>5} ({bucket_1_5/total*100:5.1f}%)")
        print(f"    6-20:   {bucket_6_20:>5} ({bucket_6_20/total*100:5.1f}%)")
        print(f"    21-50:  {bucket_21_50:>5} ({bucket_21_50/total*100:5.1f}%)")
        print(f"    51+:    {bucket_51plus:>5} ({bucket_51plus/total*100:5.1f}%)")
        print()


def main() -> None:
    words = read_words()
    analyze(words)


if __name__ == "__main__":
    main()
