# noqa: SIZE_OK - existing report script keeps its fixtures and rendering together.
"""
腕上词典 — 搜索命中率覆盖率测试脚本
模拟搜索 100 个英语 + 100 个中文（中考/高考范围）词汇，
统计直接命中、前缀命中、未命中，输出详细报告。
"""
import json, os, re, sys, time
from pathlib import Path

# ── 配置 ──
ROOT = Path(__file__).resolve().parents[1]
DICT_DIR = ROOT / "src" / "common" / "dict"
sys.path.insert(0, str(ROOT))
from scripts.generate_watch_dict import decode_delta_ids as decode_v3_ids, decode_front_code
from omo.dict_semantic_validator import read_binary_index


class DictionaryFormatError(ValueError):
    """表示生成词库中的紧凑字段不合法。"""

# ── 1. 加载词库 ──
print("=" * 60)
print("加载词库数据...")
t0 = time.time()

def decode_word_prefix(raw, prev_word):
    """Decode compact-v3 one-character Base36 front-coded words."""
    return decode_front_code(raw, prev_word)

# 加载 26 个首字母英文索引 → word set
en_word_set = set()
en_word_map = {}  # word -> (phonetic, translation, tag)
shard_count = 0
for shard_file in sorted((DICT_DIR / "words").iterdir()):
    if not shard_file.name.startswith("word_"):
        continue
    shard_count += 1
    prev_word = ""
    with open(shard_file, "r", encoding="utf-8") as f:
        for line in f:
            parts = line.strip().split("\t")
            if len(parts) == 3:
                word = decode_word_prefix(parts[0], prev_word)
                prev_word = word
                word_lower = word.lower()
                en_word_set.add(word_lower)
                en_word_map[word_lower] = ("", "", parts[2])


def decode_delta_base36(value):
    """解码 compact-v3 Base64-ULEB128 递增 entryId 列表。"""
    try:
        return decode_v3_ids(value)
    except ValueError as exc:
        raise DictionaryFormatError(str(exc)) from exc

# 加载 cn_index
cn_index = {}
cn_bucket_count = 0
cn_phrase_total = 0
for cn_file in sorted((DICT_DIR / "cn_index").iterdir()):
    if not cn_file.name.startswith("cn_"):
        continue
    cn_bucket_count += 1
    if cn_file.suffix == ".bin":
        bucket_map = {key: list(value) for key, value in read_binary_index(cn_file, "cn_index").items()}
        cn_phrase_total += len(bucket_map)
        cn_index[cn_file.stem.replace("cn_", "")] = bucket_map
        continue
    bucket_map = {}
    prev_phrase = ""
    with open(cn_file, "r", encoding="utf-8") as f:
        for line in f:
            parts = line.strip().split("\t")
            if len(parts) >= 2:
                phrase = decode_front_code(parts[0], prev_phrase)
                entry_ids = decode_delta_base36(parts[1])
                bucket_map[phrase] = entry_ids
                cn_phrase_total += 1
                prev_phrase = phrase
    cn_index[cn_file.stem.replace("cn_", "")] = bucket_map

t1 = time.time()
print(f"  英文词条总数: {len(en_word_set)}")
print(f"  英文 shard 文件: {shard_count}")
print(f"  中文索引 bucket: {cn_bucket_count}")
print(f"  中文索引词组: {cn_phrase_total}")
print(f"  加载耗时: {(t1-t0)*1000:.0f}ms")
print()

# ── 2. 定义测试词汇 ──
# 来源：中考英语666高频词 + 高考3500词（随机混合）
# 已人工排除项目词库中确定存在的词（如 ability, able, about, above 等基础词）
ENGLISH_TEST_WORDS = [
    # ---- 中考范围 (50个) ----
    "absent", "accept", "achieve", "active", "actual",
    "address", "advance", "advantage", "advertise", "afford",
    "against", "agree", "allow", "although", "announce",
    "anxious", "apologize", "appear", "apply", "appreciate",
    "argue", "arrange", "arrive", "article", "attempt",
    "attend", "attract", "average", "avoid", "awake",
    "background", "balance", "bargain", "behave", "belong",
    "benefit", "beyond", "bitter", "blame", "boil",
    "boring", "bottom", "brain", "brave", "breathe",
    "brief", "broad", "business", "cancel", "capital",
    # ---- 高考范围 (50个) ----
    "abandon", "absorb", "abstract", "abuse", "academic",
    "accelerate", "access", "accompany", "accomplish", "accurate",
    "accuse", "acknowledge", "adapt", "adjust", "administration",
    "adopt", "advanced", "adventure", "advocate", "affect",
    "aggressive", "allocate", "alternative", "amaze", "ambassador",
    "ambition", "analysis", "ancestor", "anniversary", "annual",
    "anticipate", "apparent", "appetite", "applause", "appointment",
    "approach", "appropriate", "approve", "assume", "atmosphere",
    "attach", "attempt", "attitude", "attraction", "authority",
    "available", "aware", "awkward", "bachelor", "barrier",
]

# 中文测试词（中考语文高频成语+常见词组）
# 注意：这些是英文→中文字典里的翻译可能出现的词
# 成语类相对难出现在翻译中，日常概念类更容易
CHINESE_TEST_WORDS = [
    # ---- 中考语文高频成语/词组 (50个) ----
    "喧嚣", "便捷", "慰藉", "砥砺", "跻身",
    "翱翔", "斑驳", "徜徉", "璀璨", "点缀",
    "繁衍", "俯瞰", "烘托", "荟萃", "眷恋",
    "聆听", "弥漫", "契合", "诠释", "涉猎",
    "吞噬", "陶冶", "妥帖", "寻觅", "斟酌",
    "夯实", "汲取", "缜密", "追溯", "镌刻",
    "浮躁", "谦逊", "坚韧", "豁达", "勤奋",
    "聪慧", "坦荡", "洒脱", "稳重", "严谨",
    "松懈", "懦弱", "傲慢", "吝啬", "贪婪",
    "懒惰", "虚伪", "卑鄙", "慈悲", "诚信",
    # ---- 高考/中高频抽象概念词 (50个) ----
    "福祉", "莅临", "斡旋", "彰显", "辐射",
    "凝聚", "升华", "演化", "变迁", "革新",
    "倡导", "弘扬", "摒弃", "遏制", "扭曲",
    "侵蚀", "渗透", "瓦解", "融合", "统筹",
    "兼顾", "协调", "均衡", "差异", "局限",
    "突破", "飞跃", "跨越", "门槛", "契机",
    "隐患", "弊端", "漏洞", "瓶颈", "障碍",
    "挫折", "磨难", "挑战", "机遇", "趋势",
    "格局", "维度", "层面", "体系", "机制",
    "配置", "整合", "优化", "升级", "转型",
]

if "--force-miss" in sys.argv[1:]:
    ENGLISH_TEST_WORDS[0] = "__forced_coverage_miss__"


# ── 3. 模拟搜索逻辑 ──

def search_english(word):
    """模拟英文搜索：精确匹配 + 前缀匹配"""
    low = word.lower()
    
    # 精确匹配
    if low in en_word_set:
        return ("exact", en_word_map[low])
    
    # 前缀匹配（走首字母索引扫描）
    first_char = low[0] if low else ""
    shard_file = DICT_DIR / "words" / f"word_{first_char}.txt"
    if shard_file.exists():
        prev_word = ""
        with open(shard_file, "r", encoding="utf-8") as f:
            for line in f:
                parts = line.strip().split("\t")
                if len(parts) == 3:
                    word_decoded = decode_word_prefix(parts[0], prev_word)
                    prev_word = word_decoded
                    if word_decoded.lower().startswith(low):
                        return ("prefix", ("", "", parts[2]))
    
    return ("miss", None)


def chinese_bucket_for(ch):
    """与 results.ux cnBucketFor 一致"""
    return f"{ord(ch) % 96:02x}"


def get_first_chinese_char(text):
    for ch in text:
        if '\u4e00' <= ch <= '\u9fff':
            return ch
    return ""


def has_chinese(text):
    for ch in text:
        if '\u4e00' <= ch <= '\u9fff':
            return True
    return False


def search_chinese(query):
    """模拟中文搜索：cn_index 精确 + 前缀匹配"""
    if not has_chinese(query):
        return ("miss", None)
    
    first_char = get_first_chinese_char(query)
    if not first_char:
        return ("miss", None)
    
    bucket = chinese_bucket_for(first_char)
    if bucket not in cn_index:
        return ("miss", None)
    
    index_map = cn_index[bucket]
    
    # 精确匹配
    if query in index_map:
        return ("exact", index_map[query])
    
    # 前缀匹配
    candidates = [k for k in index_map if k.startswith(query)]
    if candidates:
        # 收集所有去重 ID
        all_ids = []
        seen = set()
        for k in candidates[:20]:  # 限制20个候选 key
            for eid in index_map[k][:10]:  # 每个 key 最多10个 ID
                if eid not in seen:
                    seen.add(eid)
                    all_ids.append(eid)
        if all_ids[:50]:
            return ("prefix", all_ids[:50])
    
    return ("miss", None)


# ── 4. 执行测试 ──

def run_test(words, is_chinese=False):
    results = []
    hits_exact = 0
    hits_prefix = 0
    misses = 0
    
    for w in words:
        if is_chinese:
            kind, data = search_chinese(w)
        else:
            kind, data = search_english(w)
        
        if kind == "exact":
            hits_exact += 1
            tag = data[2] if not is_chinese else ""
        elif kind == "prefix":
            hits_prefix += 1
            tag = data[2] if not is_chinese else ""
        else:
            misses += 1
        
        results.append((w, kind, tag if kind != "miss" else ""))
    
    return results, hits_exact, hits_prefix, misses


print("=" * 60)
print("开始测试英文搜索命中率...")
print()

en_results, en_exact, en_prefix, en_miss = run_test(ENGLISH_TEST_WORDS, is_chinese=False)

print(f"英文测试: 100 词")
print(f"  精确命中: {en_exact}")
print(f"  前缀命中: {en_prefix}")
print(f"  未命中:   {en_miss}")
print(f"  总命中率: {(en_exact + en_prefix) / 100 * 100:.1f}%")
print()

# 列出未命中的英文词
missed_en = [r for r in en_results if r[1] == "miss"]
if missed_en:
    print(f"未命中的英文词 ({len(missed_en)}):")
    for i in range(0, len(missed_en), 5):
        batch = [w for w, k, t in missed_en[i:i+5]]
        print(f"  {', '.join(batch)}")
    print()

print("=" * 60)
print("开始测试中文搜索命中率...")
print()

cn_results, cn_exact, cn_prefix, cn_miss = run_test(CHINESE_TEST_WORDS, is_chinese=True)

print(f"中文测试: 100 词")
print(f"  精确命中: {cn_exact}")
print(f"  前缀命中: {cn_prefix}")
print(f"  未命中:   {cn_miss}")
print(f"  总命中率: {(cn_exact + cn_prefix) / 100 * 100:.1f}%")
print()

# 列出未命中的中文词
missed_cn = [r for r in cn_results if r[1] == "miss"]
if missed_cn:
    print(f"未命中的中文词 ({len(missed_cn)}):")
    for i in range(0, len(missed_cn), 5):
        batch = [w for w, k, t in missed_cn[i:i+5]]
        print(f"  {', '.join(batch)}")
    print()

# ── 5. 汇总报告 ──

t2 = time.time()

print("=" * 60)
print("                    覆 盖 率 测 试 报 告")
print("=" * 60)
print()
print(f"  测试时间:      {time.strftime('%Y-%m-%d %H:%M:%S')}")
print(f"  总耗时:        {(t2-t0)*1000:.0f}ms")
print()
print(f"  ┌───────────────┬──────┬──────┬──────┬──────┐")
print(f"  │ 类型          │ 总数 │ 精确 │ 前缀 │ 未命 │")
print(f"  ├───────────────┼──────┼──────┼──────┼──────┤")
print(f"  │ 英文 (中考/高考)│  100 │ {en_exact:>4} │ {en_prefix:>4} │ {en_miss:>4} │")
print(f"  │ 中文 (中考/高考)│  100 │ {cn_exact:>4} │ {cn_prefix:>4} │ {cn_miss:>4} │")
print(f"  └───────────────┴──────┴──────┴──────┴──────┘")
print()
en_hit_rate = (en_exact + en_prefix) / 100 * 100
cn_hit_rate = (cn_exact + cn_prefix) / 100 * 100
combined_rate = (en_exact + en_prefix + cn_exact + cn_prefix) / 200 * 100
print(f"  英文命中率:    {en_hit_rate:.1f}%")
print(f"  中文命中率:    {cn_hit_rate:.1f}%")
print(f"  综合命中率:    {combined_rate:.1f}%")
print()
print("─" * 60)
print("  词库概况:")
print(f"    总英文词条数:        {len(en_word_set)}")
print(f"    中文索引词组数:     {cn_phrase_total}")
print(f"    中考标签(zk):        {sum(1 for w in en_word_map if en_word_map[w][2] and int(en_word_map[w][2], 16) & (1 << 0))}")
print(f"    高考标签(gk):        {sum(1 for w in en_word_map if en_word_map[w][2] and int(en_word_map[w][2], 16) & (1 << 1))}")
print(f"    四级标签(cet4):      {sum(1 for w in en_word_map if en_word_map[w][2] and int(en_word_map[w][2], 16) & (1 << 2))}")
print(f"    六级标签(cet6):      {sum(1 for w in en_word_map if en_word_map[w][2] and int(en_word_map[w][2], 16) & (1 << 3))}")
print()

# 命中词展示
print("─" * 60)
print("  [命中示例] 英文命中词（前20个）:")
hits_en = [r for r in en_results if r[1] != "miss"][:20]
for w, k, t in hits_en:
    print(f"    {k:8s} {w}")

print()
print("─" * 60)
print("  [命中示例] 中文命中词（前20个）:")
hits_cn = [r for r in cn_results if r[1] != "miss"][:20]
for w, k, t in hits_cn:
    print(f"    {k:8s} {w}")

print()
print("=" * 60)
print("报告完毕")
print("=" * 60)

# 保存原始结果到 JSON（后续分析用）
output = {
    "meta": {
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
        "total_english_entries": len(en_word_set),
        "total_cn_phrases": cn_phrase_total,
        "cn_buckets": cn_bucket_count,
    },
    "english": {
        "total": len(ENGLISH_TEST_WORDS),
        "exact_hits": en_exact,
        "prefix_hits": en_prefix,
        "misses": en_miss,
        "hit_rate_pct": round(en_hit_rate, 1),
        "missed_words": [w for w, k, t in missed_en],
    },
    "chinese": {
        "total": len(CHINESE_TEST_WORDS),
        "exact_hits": cn_exact,
        "prefix_hits": cn_prefix,
        "misses": cn_miss,
        "hit_rate_pct": round(cn_hit_rate, 1),
        "missed_words": [w for w, k, t in missed_cn],
    },
    "combined_hit_rate": round(combined_rate, 1),
}

with open(ROOT / ".omo" / "coverage_test_result.json", "w", encoding="utf-8") as f:
    json.dump(output, f, ensure_ascii=False, indent=2)

print(f"\n详细结果已保存至 .omo/coverage_test_result.json")

count_regressions = []
if len(en_word_set) != 14_942:
    count_regressions.append(f"English headwords={len(en_word_set)} expected=14942")
if cn_phrase_total != 122_067:
    count_regressions.append(f"Chinese phrases={cn_phrase_total} expected=122067")
if shard_count != 26:
    count_regressions.append(f"word shards={shard_count} expected=26")
if cn_bucket_count != 96:
    count_regressions.append(f"Chinese buckets={cn_bucket_count} expected=96")

if en_miss or cn_miss or count_regressions:
    details = "; ".join(count_regressions) if count_regressions else "corpus sample miss"
    print(
        f"coverage validation failed: English misses={en_miss}, Chinese misses={cn_miss}; {details}",
        file=sys.stderr,
    )
    raise SystemExit(1)
