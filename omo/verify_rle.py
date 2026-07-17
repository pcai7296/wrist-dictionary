# Verify RLE encoding in zh_index files
import os

total_rle_tokens = 0
total_tokens = 0
rle_files = 0

for fname in sorted(os.listdir("src/common/dict/zh_index")):
    path = os.path.join("src/common/dict/zh_index", fname)
    with open(path, "r", encoding="utf-8") as f:
        has_rle = False
        for line in f:
            parts = line.split("\t")
            if len(parts) < 2:
                continue
            for token in parts[1].split(","):
                total_tokens += 1
                if "^" in token:
                    total_rle_tokens += 1
                    has_rle = True
        if has_rle:
            rle_files += 1

print(f"Total tokens: {total_tokens}")
print(f"RLE tokens: {total_rle_tokens}")
print(f"Files with RLE: {rle_files}/64")

# Verify decode works with the JS logic
import re

def parse_base36(s):
    result = 0
    for ch in s:
        code = ord(ch)
        digit = code - 48 if 48 <= code <= 57 else code - 87
        if digit < 0 or digit >= 36:
            return -1
        result = result * 36 + digit
    return result

def decode_delta_ids(value):
    if not isinstance(value, str):
        return []
    normalized = value.strip()
    if not normalized:
        return []
    tokens = normalized.split(",")
    ids = []
    current_id = 0
    first_token = True
    for token in tokens:
        if not token:
            return []
        caret_idx = token.find("^")
        if caret_idx >= 0:
            val_str = token[:caret_idx]
            count_str = token[caret_idx + 1:]
            if not val_str or not count_str or not re.match(r"^[0-9a-z]+$", val_str) or not re.match(r"^[1-9][0-9]*$", count_str):
                return []
            repeat = int(count_str)
            if repeat < 2 or repeat > 200:
                return []
            delta = parse_base36(val_str)
            if delta < 0:
                return []
        else:
            if not re.match(r"^[0-9a-z]+$", token):
                return []
            delta = parse_base36(token)
            if delta < 0:
                return []
            repeat = 1

        if not first_token and delta == 0:
            return []
        first_token = False

        for _ in range(repeat):
            current_id += delta
            ids.append(current_id)
    return ids

# Test decode on every line
errors = []
total_chars = 0
for fname in sorted(os.listdir("src/common/dict/zh_index")):
    path = os.path.join("src/common/dict/zh_index", fname)
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            parts = line.split("\t")
            if len(parts) < 2:
                continue
            total_chars += 1
            ids = decode_delta_ids(parts[1])
            if not ids:
                errors.append(f"{fname}: \"{parts[0]}\" decode failed: {parts[1][:60]}")
            elif len(ids) != len(set(ids)):
                errors.append(f"{fname}: \"{parts[0]}\" has duplicates")
            elif ids != sorted(ids):
                errors.append(f"{fname}: \"{parts[0]}\" not sorted")

print(f"\nChars decoded: {total_chars}")
if errors:
    print(f"\nERRORS ({len(errors)}):")
    for e in errors[:10]:
        print(f"  {e}")
else:
    print("All decodes valid ✅")

# Verify old decoder still works on non-RLE data
def old_decode_delta_ids(value):
    normalized = value.strip()
    tokens = normalized.split(",")
    ids = []
    current_id = 0
    for i, token in enumerate(tokens):
        if not re.match(r"^[0-9a-z]+$", token):
            return []
        delta = parse_base36(token)
        if delta < 0:
            return []
        if i > 0 and delta == 0:
            return []
        current_id += delta
        ids.append(current_id)
    return ids

# Compare old vs new for files without RLE
same_count = 0
for fname in sorted(os.listdir("src/common/dict/zh_index")):
    path = os.path.join("src/common/dict/zh_index", fname)
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            parts = line.split("\t")
            if len(parts) < 2:
                continue
            if "^" not in parts[1]:
                old = old_decode_delta_ids(parts[1])
                new = decode_delta_ids(parts[1])
                if old == new:
                    same_count += 1
                else:
                    print(f"MISMATCH: {fname} \"{parts[0]}\" old={old[:5]} new={new[:5]}")

print(f"\nNon-RLE lines matching old decoder: {same_count}")
