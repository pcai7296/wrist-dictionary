# Analyze RLE potential for cn_index and overall compression opportunities
import os

# cn_index analysis
total_cn_size = 0
total_cn_deltas = 0
cn_ones = 0

for fname in sorted(os.listdir("src/common/dict/cn_index")):
    path = os.path.join("src/common/dict/cn_index", fname)
    total_cn_size += os.path.getsize(path)
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            parts = line.split("\t")
            if len(parts) < 2:
                continue
            ids = parts[1].split(",")
            total_cn_deltas += len(ids)
            cn_ones += sum(1 for d in ids if d == "1")

print(f"cn_index: {total_cn_size/1024:.1f} KB, {total_cn_deltas} deltas")
print(f"  '1' deltas: {cn_ones} ({cn_ones/total_cn_deltas*100:.1f}%)")

# zh_index size
total_zh_size = 0
for fname in sorted(os.listdir("src/common/dict/zh_index")):
    total_zh_size += os.path.getsize(os.path.join("src/common/dict/zh_index", fname))
print(f"\nzh_index: {total_zh_size/1024:.1f} KB")

# Inflect sizes
inflect_size = sum(
    os.path.getsize(os.path.join("src/common/dict/inflect", f))
    for f in os.listdir("src/common/dict/inflect")
)
inflect_rev_size = sum(
    os.path.getsize(os.path.join("src/common/dict/inflect_reverse", f))
    for f in os.listdir("src/common/dict/inflect_reverse")
)
print(f"inflect: {inflect_size/1024:.1f} KB")
print(f"inflect_reverse: {inflect_rev_size/1024:.1f} KB")

# Entries size
entries_size = sum(
    os.path.getsize(os.path.join("src/common/dict/entries", f))
    for f in os.listdir("src/common/dict/entries")
)
print(f"entries: {entries_size/1024:.1f} KB")

# Words size
words_size = sum(
    os.path.getsize(os.path.join("src/common/dict/words", f))
    for f in os.listdir("src/common/dict/words")
)
print(f"words: {words_size/1024:.1f} KB")

meta_size = os.path.getsize("src/common/dict/meta.json")
total = total_cn_size + total_zh_size + inflect_size + inflect_rev_size + entries_size + words_size + meta_size
print(f"\nTotal dict: {total/1024:.1f} KB ({total:,} bytes)")

# Check if consolidate zh_index from 64 -> 1 (single file)
# Each file has filesystem overhead ~4KB
filesystem_overhead = 64 * 4
print(f"\nFilesystem overhead (64 files * 4KB): {filesystem_overhead} KB")
print(f"If consolidated to 1 file: save {filesystem_overhead - 4} KB in overhead")

# How many unique chars per bucket?
bucket_counts = {}
for fname in sorted(os.listdir("src/common/dict/zh_index")):
    path = os.path.join("src/common/dict/zh_index", fname)
    with open(path, "r", encoding="utf-8") as f:
        lines = [l for l in f if l.strip()]
    bucket_counts[fname] = len(lines)
print(f"\nChars per zh_index bucket:")
print(f"  Min: {min(bucket_counts.values())}, Max: {max(bucket_counts.values())}")
print(f"  Avg: {sum(bucket_counts.values())/len(bucket_counts):.0f}")
empty_buckets = sum(1 for v in bucket_counts.values() if v == 0)
print(f"  Empty buckets: {empty_buckets}")
