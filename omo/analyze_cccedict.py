"""
Analyze CC-CEDICT and test integration with existing dictionary.
Output: practical stats for decision making.
"""
import csv, gzip, json, os, re, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TEMP = os.environ["TEMP"]
DICT_DIR = ROOT / "src" / "common" / "dict"
sys.path.insert(0, str(ROOT))
from scripts.generate_watch_dict import decode_front_code
from omo.dict_semantic_validator import read_binary_index

# ── 1. Parse CC-CEDICT ──
CCEDICT_PATH = TEMP + "\\cedict.txt.gz"
with gzip.open(CCEDICT_PATH, "rt", encoding="utf-8") as f:
    lines = f.readlines()

entries = [l.strip() for l in lines if l.strip() and not l.startswith("#")]
print(f"CC-CEDICT total entries: {len(entries)}")

# Parse each entry: Traditional Simplified [pin1 yin1] /meaning1/meaning2/
parsed = []
for entry in entries:
    # Split on first '[' to separate Chinese part from pinyin
    bracket_pos = entry.find("[")
    slash_pos = entry.find("/")
    if bracket_pos < 0 or slash_pos < 0:
        continue
    chinese_part = entry[:bracket_pos].strip()
    # English starts after last ']' before first '/'
    english_start = entry.rfind("]", 0, slash_pos)
    if english_start < 0:
        continue
    english_text = entry[slash_pos:]  # / meaning1 / meaning2 /
    meanings = [m.strip() for m in english_text.split("/") if m.strip()]

    # Chinese: "Traditional Simplified"
    trad_simp = chinese_part.split()
    if len(trad_simp) < 2:
        continue
    simplified = trad_simp[1]
    # Extract only Chinese chars
    cn_chars = re.findall(r"[\u4e00-\u9fff]+", simplified)
    chinese_phrase = "".join(cn_chars)
    if len(chinese_phrase) < 2:
        continue

    parsed.append((chinese_phrase, meanings))

print(f"Parsed entries (2+ Chinese chars): {len(parsed)}")

# ── 2. Load existing dictionary word set ──
print("\nLoading existing dictionary...")
def decode_word_prefix(raw, prev_word):
    """Decode compact-v3 one-character Base36 front-coded words."""
    return decode_front_code(raw, prev_word)

en_word_set = set()
for shard_file in sorted((DICT_DIR / "words").iterdir()):
    if not shard_file.name.startswith("word_"):
        continue
    prev_word = ""
    with open(shard_file, "r", encoding="utf-8") as f:
        for line in f:
            parts = line.strip().split("\t")
            if len(parts) == 3:
                word = decode_word_prefix(parts[0], prev_word)
                prev_word = word
                en_word_set.add(word.lower().strip())

print(f"Existing English words: {len(en_word_set)}")

# ── 3. Build zh2en mapping ──
# For each Chinese phrase in CC-CEDICT, find English words that exist in our dict
# Count how many would be NEW additions to cn_index

# First, build existing cn_index phrases
existing_cn_phrases = set()
for cn_file in sorted((DICT_DIR / "cn_index").iterdir()):
    if not cn_file.name.startswith("cn_"):
        continue
    if cn_file.suffix == ".bin":
        existing_cn_phrases.update(read_binary_index(cn_file, "cn_index"))
        continue
    with open(cn_file, "r", encoding="utf-8") as f:
        for line in f:
            parts = line.strip().split("\t")
            if len(parts) >= 2:
                existing_cn_phrases.add(parts[0])

print(f"Existing cn_index phrases: {len(existing_cn_phrases)}")

# Now for each CC-CEDICT entry, find English words that map to our dictionary
# and count how many NEW Chinese phrases this would add
new_phrases = 0
new_phrase_words = {}  # sample new phrases -> English words
total_mappable_entries = 0
phrase_mapped_words = {}  # phrase -> set of english words that map to our dict

for phrase, meanings in parsed:
    mappable_words = set()
    for meaning in meanings:
        # Extract first word (usually the headword)
        words = re.findall(r"[a-zA-Z]+", meaning.lower())
        for w in words:
            if w in en_word_set:
                mappable_words.add(w)

    if mappable_words:
        total_mappable_entries += 1
        if phrase not in existing_cn_phrases:
            new_phrases += 1
            if len(new_phrase_words) < 20:
                new_phrase_words[phrase] = list(mappable_words)[:5]
        if phrase not in new_phrase_words and len(new_phrase_words) < 40:
            pass  # just for sampling
        phrase_mapped_words[phrase] = mappable_words

# Sample new phrases
samples = [(p, list(w)[:5]) for p, w in phrase_mapped_words.items()
           if p not in existing_cn_phrases][:25]

# Count phrase-word pairs
all_cn_from_cc = set(phrase for phrase, _ in parsed)
new_cn_count = len(all_cn_from_cc - existing_cn_phrases)
total_cn_after = len(existing_cn_phrases | all_cn_from_cc)

# ── 4. Report ──
print(f"\n{'='*60}")
print(f"              CC-CEDICT 融合分析报告")
print(f"{'='*60}")
print(f"\n  CC-CEDICT 概况:")
print(f"    原始词条数:           {len(entries)}")
print(f"    有效解析(2字+词组):   {len(parsed)}")
print(f"    唯一中文词组:         {len(all_cn_from_cc)}")
print(f"\n  与现有词库匹配分析:")
print(f"    能映射到现有英文词:   {total_mappable_entries}")
print(f"    现有 cn_index 词组:   {len(existing_cn_phrases)}")
print(f"    CC-CEDICT 新增词组:   {new_cn_count}")
print(f"    融合后 cn_index 总量: {total_cn_after}")
print(f"    中文覆盖率提升:       +{new_cn_count / len(existing_cn_phrases) * 100:.1f}%")
print(f"\n  [新增词组示例] (前25个):")
for phrase, words in samples:
    print(f"    {phrase} → {', '.join(words)}")

# What percentage of the 36 missed Chinese words would be covered?
print(f"\n  [针对之前测试未命中36词的覆盖分析]:")
# Read the missed words
missed = ["便捷", "慰藉", "砥砺", "跻身", "璀璨", "繁衍", "眷恋", "聆听",
          "契合", "诠释", "吞噬", "妥帖", "寻觅", "缜密", "镌刻", "浮躁",
          "豁达", "聪慧", "坦荡", "洒脱", "诚信", "福祉", "莅临", "彰显",
          "弘扬", "兼顾", "局限", "契机", "隐患", "弊端", "格局", "维度",
          "层面", "机制", "整合", "转型"]

new_hits = 0
for m in missed:
    if m in phrase_mapped_words:
        new_hits += 1
        print(f"    ✅ {m} → {', '.join(list(phrase_mapped_words[m])[:5])}")
    elif m in all_cn_from_cc:
        print(f"    ⚠️ {m} (在CC-CEDICT中，但无对应词库英文词)")
    else:
        print(f"    ❌ {m} (CC-CEDICT中也没有)")

print(f"\n    36个未命中词中, CC-CEDICT可覆盖: {new_hits}/{len(missed)}")
print(f"    中文命中率预期提升: 64% → {(60+4+new_hits)/100*100:.1f}%")

# Size estimate
print(f"\n  [体积估算]:")
cc_full_size = sum(len(p.encode("utf-8")) + sum(len(w.encode("utf-8")) + 2 for w in ws) for p, ws in phrase_mapped_words.items())
# Each entry: phrase\tword1,word2,...\n
per_entry = sum(len(p.encode("utf-8")) + 1 + sum(len(w.encode("utf-8")) for w in ws) + len(ws) - 1 + 1 for p, ws in phrase_mapped_words.items())
print(f"    新增索引原始大小:    ~{per_entry // 1024}KB")
# Estimate per-bucket size (64 buckets)
print(f"    分64 bucket后每个:   ~{per_entry // 64 // 1024}KB")
