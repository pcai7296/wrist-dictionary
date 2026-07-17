# Analyze RLE potential for zh_index
import os
from collections import Counter

total_deltas = 0
all_runs = []
current_run = 0
current_val = None

for fname in sorted(os.listdir("src/common/dict/zh_index")):
    path = os.path.join("src/common/dict/zh_index", fname)
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            parts = line.split("\t")
            if len(parts) < 2:
                continue
            for d in parts[1].split(","):
                total_deltas += 1
                if d == current_val:
                    current_run += 1
                else:
                    if current_run > 1:
                        all_runs.append((current_val, current_run))
                    current_val = d
                    current_run = 1

print(f"Total deltas: {total_deltas}")
print(f"Total runs >1: {len(all_runs)}")
total_in_runs = sum(r for _, r in all_runs)
print(f"Deltas in runs >1: {total_in_runs} ({total_in_runs/total_deltas*100:.1f}%)")
total_savings = sum(r - 2 for _, r in all_runs)
print(f"Estimated RLE savings: {total_savings} tokens saved")
print(f"RLE token count: {total_deltas - total_savings}")
print(f"Max run: {max(r for _, r in all_runs)}")

# Distribution of run lengths
run_len_dist = Counter(r for _, r in all_runs)
for length in sorted(run_len_dist):
    print(f"  Run length {length}: {run_len_dist[length]} runs")

# What values repeat?
val_dist = Counter()
for val, r in all_runs:
    val_dist[val] += 1
print("\nTop 10 run values:")
for val, count in val_dist.most_common(10):
    total_in_val = sum(r for v, r in all_runs if v == val)
    print(f'  "{val}": {count} runs, {total_in_val} total tokens')
