"""
腕上词典 — 覆盖率测试 V2（全新测试词，不重复上次）
"""
import json, os, re, sys, time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DICT_DIR = ROOT / "src" / "common" / "dict"
sys.path.insert(0, str(ROOT))
from scripts.generate_watch_dict import decode_delta_ids, decode_front_code

# ── 上次用过的词 (排除这些) ──
PREVIOUS_ENGLISH = {
    "absent", "accept", "achieve", "active", "actual", "address", "advance",
    "advantage", "advertise", "afford", "against", "agree", "allow",
    "although", "announce", "anxious", "apologize", "appear", "apply",
    "appreciate", "argue", "arrange", "arrive", "article", "attempt",
    "attend", "attract", "average", "avoid", "awake", "background",
    "balance", "bargain", "behave", "belong", "benefit", "beyond",
    "bitter", "blame", "boil", "boring", "bottom", "brain", "brave",
    "breathe", "brief", "broad", "business", "cancel", "capital",
    "abandon", "absorb", "abstract", "abuse", "academic", "accelerate",
    "access", "accompany", "accomplish", "accurate", "accuse",
    "acknowledge", "adapt", "adjust", "administration", "adopt",
    "advanced", "adventure", "advocate", "affect", "aggressive",
    "allocate", "alternative", "amaze", "ambassador", "ambition",
    "analysis", "ancestor", "anniversary", "annual", "anticipate",
    "apparent", "appetite", "applause", "appointment", "approach",
    "appropriate", "approve", "assume", "atmosphere", "attach",
    "attitude", "attraction", "authority", "available", "aware",
    "awkward", "bachelor", "barrier",
}

PREVIOUS_CHINESE = {
    "喧嚣", "便捷", "慰藉", "砥砺", "跻身", "翱翔", "斑驳", "徜徉", "璀璨",
    "点缀", "繁衍", "俯瞰", "烘托", "荟萃", "眷恋", "聆听", "弥漫", "契合",
    "诠释", "涉猎", "吞噬", "陶冶", "妥帖", "寻觅", "斟酌", "夯实", "汲取",
    "缜密", "追溯", "镌刻", "浮躁", "谦逊", "坚韧", "豁达", "勤奋", "聪慧",
    "坦荡", "洒脱", "稳重", "严谨", "松懈", "懦弱", "傲慢", "吝啬", "贪婪",
    "懒惰", "虚伪", "卑鄙", "慈悲", "诚信", "福祉", "莅临", "斡旋", "彰显",
    "辐射", "凝聚", "升华", "演化", "变迁", "革新", "倡导", "弘扬", "摒弃",
    "遏制", "扭曲", "侵蚀", "渗透", "瓦解", "融合", "统筹", "兼顾", "协调",
    "均衡", "差异", "局限", "突破", "飞跃", "跨越", "门槛", "契机", "隐患",
    "弊端", "漏洞", "瓶颈", "障碍", "挫折", "磨难", "挑战", "机遇", "趋势",
    "格局", "维度", "层面", "体系", "机制", "配置", "整合", "优化", "升级",
    "转型",
}

# ── 全新100个英文测试词（中考50+高考50，与上次零重叠）──
NEW_ENGLISH = [
    # 中考范围 (50个，new)
    "amazing", "ancient", "balloon", "basic", "candle",
    "century", "challenge", "dangerous", "deaf", "describe",
    "dictionary", "disappoint", "effort", "empty", "energy",
    "familiar", "garden", "harm", "imagine", "important",
    "journey", "knowledge", "language", "magazine", "necessary",
    "offer", "opinion", "paint", "pour", "raise",
    "rapid", "reason", "regret", "remind", "repair",
    "require", "sandwich", "satisfy", "scientist", "admire",
    "ahead", "accidentally", "appointment", "abundant", "caution",
    "complete", "connect", "consider", "courage", "create",
    # 高考范围 (50个，new)
    "acquire", "accumulate", "absence", "abundance", "ambiguous",
    "arbitrary", "authentic", "cautious", "compulsory", "contribute",
    "convention", "convey", "coordinate", "correspond", "counsel",
    "cultivate", "curiosity", "debate", "decade", "decline",
    "decorate", "decrease", "dedicate", "defeat", "defense",
    "deficit", "demonstrate", "deny", "depart", "deposit",
    "derive", "deserve", "desperate", "destination", "device",
    "devote", "dignity", "dilemma", "dimension", "diminish",
    "diploma", "diplomatic", "discipline", "discount", "display",
    "distinguish", "distort", "distribute", "domestic", "dominant",
]

# ── 全新100个中文测试词（与上次零重叠) ──
NEW_CHINESE = [
    # 中考常考成语/词语 (50个，new)
    "安然无恙", "百折不挠", "不耻下问", "不屈不挠", "持之以恒",
    "大公无私", "废寝忘食", "光明磊落", "精益求精", "博览群书",
    "不求甚解", "举一反三", "勤学好问", "融会贯通", "水滴石穿",
    "按图索骥", "不翼而飞", "一言不发", "一帆风顺", "一针见血",
    "不可思议", "东山再起", "人山人海", "以身作则", "以卵击石",
    "津津有味", "井井有条", "面目全非", "莫名其妙", "络绎不绝",
    "落英缤纷", "茅塞顿开", "美不胜收", "妙笔生花", "名副其实",
    "念念不忘", "迫不及待", "情不自禁", "异口同声", "引人注目",
    "与日俱增", "语重心长", "再接再厉", "斩钉截铁", "朝气蓬勃",
    "知难而退", "专心致志", "自力更生", "走马观花", "半途而废",
    # 现代常用词组/抽象概念 (50个，new)
    "自律", "包容", "同理心", "执行力", "凝聚力",
    "认同感", "归属感", "幸福感", "使命感", "紧迫感",
    "主导权", "话语权", "定价权", "裁判权", "主导",
    "衍生", "赋能", "迭代", "闭环", "对齐",
    "落地", "复盘", "复盘", "联动", "杠杆",
    "边际", "阈值", "范式", "属性", "变量",
    "常量", "基准", "锚点", "拐点", "红利",
    "产能", "业态", "链路", "画像", "漏斗",
    "曝光", "留存", "转化", "渗透率", "周转率",
    "使用率", "覆盖率", "增长率", "贡献率", "成功率",
]

# 去重——确保和上次完全不重叠
NEW_ENGLISH = [w for w in NEW_ENGLISH if w not in PREVIOUS_ENGLISH]
NEW_CHINESE = [w for w in NEW_CHINESE if w not in PREVIOUS_CHINESE]
# 去重自身
NEW_ENGLISH = list(dict.fromkeys(NEW_ENGLISH))
NEW_CHINESE = list(dict.fromkeys(NEW_CHINESE))

print(f"英文测试词: {len(NEW_ENGLISH)} (去重后)")
print(f"中文测试词: {len(NEW_CHINESE)} (去重后)")

# ── 加载词库 ──
print("\n加载词库...")
t0 = time.time()

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

# cn_index
cn_index = {}
for cn_file in sorted((DICT_DIR / "cn_index").iterdir()):
    if not cn_file.name.startswith("cn_"):
        continue
    bucket_map = {}
    prev_phrase = ""
    with open(cn_file, "r", encoding="utf-8") as f:
        for line in f:
            parts = line.strip().split("\t")
            if len(parts) >= 2:
                phrase = decode_front_code(parts[0], prev_phrase)
                bucket_map[phrase] = decode_delta_ids(parts[1])
                prev_phrase = phrase
    cn_index[cn_file.stem.replace("cn_", "")] = bucket_map

print(f"  英文词条: {len(en_word_set)}")
print(f"  cn_index词组: {sum(len(v) for v in cn_index.values())}")

# ── 搜索函数 ──
def search_english(word):
    low = word.lower().strip()
    if low in en_word_set:
        return "exact"
    # prefix match
    shard_file = DICT_DIR / "words" / f"word_{low[:1]}.txt"
    if shard_file.exists():
        prev_word = ""
        with open(shard_file, "r", encoding="utf-8") as f:
            for line in f:
                parts = line.strip().split("\t")
                if len(parts) == 3:
                    word_decoded = decode_word_prefix(parts[0], prev_word)
                    prev_word = word_decoded
                    if word_decoded.lower().startswith(low):
                        return "prefix"
    return "miss"

def zh_bucket(ch):
    return f"{ord(ch) % 96:02x}"

def search_chinese(phrase):
    first = ""
    for ch in phrase:
        if '\u4e00' <= ch <= '\u9fff':
            first = ch
            break
    if not first:
        return "miss"
    bucket = zh_bucket(first)
    if bucket not in cn_index:
        return "miss"
    im = cn_index[bucket]
    if phrase in im:
        return "exact"
    for k in im:
        if k.startswith(phrase):
            return "prefix"
    return "miss"

# ── 运行测试 ──
en_exact = en_prefix = en_miss = 0
en_details = []
for w in NEW_ENGLISH[:100]:
    r = search_english(w)
    en_details.append((w, r))
    if r == "exact":
        en_exact += 1
    elif r == "prefix":
        en_prefix += 1
    else:
        en_miss += 1

cn_exact = cn_prefix = cn_miss = 0
cn_details = []
for w in NEW_CHINESE[:100]:
    r = search_chinese(w)
    cn_details.append((w, r))
    if r == "exact":
        cn_exact += 1
    elif r == "prefix":
        cn_prefix += 1
    else:
        cn_miss += 1

# ── 报告 ──
print(f"\n{'='*60}")
print(f"             覆 盖 率 测 试 V2")
print(f"{'='*60}")
print(f"  总耗时: {(time.time()-t0)*1000:.0f}ms")
print()
print(f"  ┌───────────────┬──────┬──────┬──────┬──────┐")
print(f"  │ 类型          │ 总数 │ 精确 │ 前缀 │ 未命 │")
print(f"  ├───────────────┼──────┼──────┼──────┼──────┤")
print(f"  │ 英文(全新)    │  {len(NEW_ENGLISH[:100]):>4} │ {en_exact:>4} │ {en_prefix:>4} │ {en_miss:>4} │")
print(f"  │ 中文(全新)    │  {len(NEW_CHINESE[:100]):>4} │ {cn_exact:>4} │ {cn_prefix:>4} │ {cn_miss:>4} │")
print(f"  └───────────────┴──────┴──────┴──────┴──────┘")
print()
en_rate = (en_exact + en_prefix) / min(len(NEW_ENGLISH), 100) * 100
cn_rate = (cn_exact + cn_prefix) / min(len(NEW_CHINESE), 100) * 100
print(f"  英文命中率: {en_rate:.1f}%")
print(f"  中文命中率: {cn_rate:.1f}%")

# 未命中列表
missed_en = [w for w, r in en_details[:100] if r == "miss"]
missed_cn = [w for w, r in cn_details[:100] if r == "miss"]
if missed_en:
    print(f"\n  英文未命中 ({len(missed_en)}): {', '.join(missed_en)}")
if missed_cn:
    print(f"\n  中文未命中 ({len(missed_cn)}): {', '.join(missed_cn)}")
if not missed_en and not missed_cn:
    print(f"\n  ✅ 全部命中！零遗漏。")

print()
print(f"{'='*60}")
print(f"  对比上次:")
print(f"    英文: 100.0% → {en_rate:.1f}%  (词库未变)")
print(f"    中文:  64.0% → {cn_rate:.1f}%  (集成CC-CEDICT后)")
print(f"{'='*60}")

# 保存
result = {
    "version": 2,
    "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
    "english": {"total": min(len(NEW_ENGLISH), 100), "exact": en_exact, "prefix": en_prefix, "miss": en_miss, "rate": round(en_rate, 1)},
    "chinese": {"total": min(len(NEW_CHINESE), 100), "exact": cn_exact, "prefix": cn_prefix, "miss": cn_miss, "rate": round(cn_rate, 1)},
    "missed_english": missed_en,
    "missed_chinese": missed_cn,
}
with open(ROOT / ".omo" / "coverage_test_v2.json", "w", encoding="utf-8") as f:
    json.dump(result, f, ensure_ascii=False, indent=2)
print(f"\n结果保存到 .omo/coverage_test_v2.json")
