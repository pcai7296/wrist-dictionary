import csv
import json
import re
import shutil
import xml.etree.ElementTree as ET
from zipfile import ZipFile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "data" / "ecdict_tagged_14942_compact.csv"
WORD_FAMILY_SOURCE = ROOT / "data" / "bnc_coca_word_family_lists_v2.xlsx"
WORD_FAMILY_SOURCE_URL = "https://www.eapfoundation.com/vocab/general/bnccoca/"
OUT = ROOT / "src" / "common" / "dict"
ENTRY_SHARD_SIZE = 500
ZH_BUCKET_COUNT = 64
XLSX_NS = {"a": "http://schemas.openxmlformats.org/spreadsheetml/2006/main"}


def clean_text(value):
    value = (value or "").replace("\r", "\n")
    value = value.replace("\\n", "; ")
    value = re.sub(r"\s*\n\s*", "; ", value)
    value = value.replace("\t", " ")
    value = re.sub(r"\s+", " ", value)
    return value.strip()


def key_for(value):
    value = (value or "").lower().strip()
    chars = []
    for char in value:
        if ("a" <= char <= "z") or ("0" <= char <= "9"):
            chars.append(char)
        else:
            chars.append("_")
        if len(chars) == 2:
            break
    while len(chars) < 2:
        chars.append("_")
    return "".join(chars)


def normalize_chinese(value):
    return "".join(re.findall(r"[\u4e00-\u9fff]", value or ""))


def zh_bucket_for(char):
    return f"{ord(char) % ZH_BUCKET_COUNT:02x}"


def entry_shard_for(entry_id):
    return f"{entry_id // ENTRY_SHARD_SIZE:02d}"


def parse_exchange(exchange):
    forms = []
    for part in (exchange or "").split("/"):
        if ":" not in part:
            continue
        _, value = part.split(":", 1)
        value = value.strip()
        if value:
            forms.append(value)
    return forms


def normalize_family_word(value):
    value = (value or "").lower().strip()
    value = re.sub(r"\s+", " ", value)
    if not re.fullmatch(r"[a-z][a-z0-9'-]*", value):
        return ""
    return value


def parse_related_forms(value):
    forms = []
    for part in (value or "").split(","):
        word = re.sub(r"\s*\([^()]*\)\s*$", "", part).strip()
        word = normalize_family_word(word)
        if word:
            forms.append(word)
    return forms


def cell_column(ref):
    letters = re.sub(r"[^A-Z]", "", ref or "")
    value = 0
    for char in letters:
        value = value * 26 + ord(char) - ord("A") + 1
    return value


def load_shared_strings(zip_file):
    if "xl/sharedStrings.xml" not in zip_file.namelist():
        return []
    root = ET.fromstring(zip_file.read("xl/sharedStrings.xml"))
    strings = []
    for item in root.findall("a:si", XLSX_NS):
        texts = []
        for text in item.findall(".//a:t", XLSX_NS):
            texts.append(text.text or "")
        strings.append("".join(texts))
    return strings


def read_xlsx_rows(path):
    rows = []
    with ZipFile(path) as zip_file:
        shared_strings = load_shared_strings(zip_file)
        root = ET.fromstring(zip_file.read("xl/worksheets/sheet1.xml"))
        for row in root.findall(".//a:row", XLSX_NS):
            values = {}
            for cell in row.findall("a:c", XLSX_NS):
                ref = cell.attrib.get("r", "")
                column = cell_column(ref)
                kind = cell.attrib.get("t", "")
                raw = ""
                value_node = cell.find("a:v", XLSX_NS)
                if value_node is not None and value_node.text:
                    raw = value_node.text
                if kind == "s" and raw:
                    raw = shared_strings[int(raw)]
                elif kind == "inlineStr":
                    raw = "".join(text.text or "" for text in cell.findall(".//a:t", XLSX_NS))
                values[column] = raw
            rows.append(values)
    return rows


def load_word_family_links(word_set):
    stats = {
        "available": WORD_FAMILY_SOURCE.exists(),
        "source": str(WORD_FAMILY_SOURCE),
        "sourceUrl": WORD_FAMILY_SOURCE_URL,
        "rows": 0,
        "matchedRows": 0,
        "candidateLinks": 0,
        "matchedLinks": 0,
        "links": [],
    }
    if not WORD_FAMILY_SOURCE.exists():
        return stats

    links = set()
    for row in read_xlsx_rows(WORD_FAMILY_SOURCE):
        base = normalize_family_word(row.get(2, ""))
        related = row.get(3, "")
        if not base or not related:
            continue
        if base == "headword":
            continue
        stats["rows"] += 1
        if base not in word_set:
            continue
        stats["matchedRows"] += 1
        for form in parse_related_forms(related):
            if form == base:
                continue
            stats["candidateLinks"] += 1
            if form in word_set:
                links.add((form, base))

    stats["links"] = sorted(links)
    stats["matchedLinks"] = len(stats["links"])
    return stats


def derived_candidates(word):
    candidates = []
    if word.endswith("ily") and len(word) > 5:
        candidates.append(word[:-3] + "y")
    if word.endswith("ly") and len(word) > 5:
        candidates.append(word[:-2])
    if word.endswith("iness") and len(word) > 7:
        candidates.append(word[:-5] + "y")
    if word.endswith("ness") and len(word) > 6:
        candidates.append(word[:-4])
    if word.endswith("ment") and len(word) > 7:
        candidates.append(word[:-4])
    if word.endswith("able") and len(word) > 8:
        candidates.append(word[:-4])
        candidates.append(word[:-4] + "e")
    if word.endswith("ible") and len(word) > 8:
        candidates.append(word[:-4])
    if word.endswith("ful") and len(word) > 6:
        candidates.append(word[:-3])
        if word.endswith("iful"):
            candidates.append(word[:-4] + "y")
    if word.endswith("less") and len(word) > 7:
        candidates.append(word[:-4])
    if word.endswith("hood") and len(word) > 7:
        candidates.append(word[:-4])
    if word.endswith("ship") and len(word) > 7:
        candidates.append(word[:-4])
    if word.endswith("er") and len(word) > 6:
        candidates.append(word[:-2])
    if word.endswith("or") and len(word) > 6:
        candidates.append(word[:-2])
        candidates.append(word[:-2] + "e")
    return candidates


def load_rule_links(word_set):
    links = set()
    for word in word_set:
        for base in derived_candidates(word):
            if base in word_set and base != word:
                links.add((word, base))
    return sorted(links)


def main():
    rows = []
    with SOURCE.open("r", encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle)
        for row in reader:
            word = clean_text(row.get("word"))
            if not word:
                continue
            rows.append(
                {
                    "word": word,
                    "phonetic": clean_text(row.get("phonetic")),
                    "translation": clean_text(row.get("translation")),
                    "tag": clean_text(row.get("tag")),
                    "exchange": clean_text(row.get("exchange")),
                }
            )

    if OUT.exists():
        shutil.rmtree(OUT)
    (OUT / "words").mkdir(parents=True)
    (OUT / "inflect").mkdir(parents=True)
    (OUT / "entries").mkdir(parents=True)
    (OUT / "zh_index").mkdir(parents=True)
    (OUT / "inflect_reverse").mkdir(parents=True)

    word_shards = {}
    first_index = {}
    inflect = {}
    reverse_inflect = {}
    entry_shards = {}
    zh_index = {}
    word_set = {row["word"].lower() for row in rows}
    exchange_links = 0
    word_family_links_added = 0

    def add_inflect_link(form, base):
        form = normalize_family_word(form)
        base = normalize_family_word(base)
        if not form or not base or form == base:
            return False
        form_key = key_for(form)
        rev_key = key_for(base)
        before = len(inflect.setdefault(form_key, {}).setdefault(form, set()))
        inflect[form_key][form].add(base)
        reverse_inflect.setdefault(rev_key, {}).setdefault(base, set()).add(form)
        return len(inflect[form_key][form]) > before

    for entry_id, row in enumerate(rows):
        shard = key_for(row["word"])
        word_shards.setdefault(shard, []).append(row)
        first_index.setdefault(shard[0], set()).add(shard)
        entry_shard = entry_shard_for(entry_id)
        entry_shards.setdefault(entry_shard, []).append((entry_id, row))

        zh_text = normalize_chinese(row["translation"])
        for char in sorted(set(zh_text)):
            bucket = zh_bucket_for(char)
            zh_index.setdefault(bucket, {}).setdefault(char, []).append(entry_id)

        word_lower = row["word"].lower()
        for form in parse_exchange(row["exchange"]):
            if add_inflect_link(form, word_lower):
                exchange_links += 1

    word_family_stats = load_word_family_links(word_set)
    for form, base in word_family_stats["links"]:
        if add_inflect_link(form, base):
            word_family_links_added += 1

    rule_links = load_rule_links(word_set)
    rule_links_added = 0
    for form, base in rule_links:
        if add_inflect_link(form, base):
            rule_links_added += 1

    for shard, shard_rows in sorted(word_shards.items()):
        shard_rows.sort(key=lambda item: item["word"].lower())
        lines = []
        for row in shard_rows:
            lines.append(
                "\t".join(
                    [
                        row["word"],
                        row["phonetic"],
                        row["translation"],
                        row["tag"],
                        row["exchange"],
                    ]
                )
            )
        (OUT / "words" / f"dict_{shard}.txt").write_text("\n".join(lines) + "\n", encoding="utf-8")

    index_lines = []
    for first, shards in sorted(first_index.items()):
        index_lines.append(first + "\t" + ",".join(sorted(shards)))
    (OUT / "index_en.txt").write_text("\n".join(index_lines) + "\n", encoding="utf-8")

    for shard, forms in sorted(inflect.items()):
        lines = []
        for form, bases in sorted(forms.items()):
            lines.append(form + "\t" + ",".join(sorted(bases)))
        (OUT / "inflect" / f"inflect_{shard}.txt").write_text("\n".join(lines) + "\n", encoding="utf-8")

    for shard, bases in sorted(reverse_inflect.items()):
        lines = []
        for base, forms in sorted(bases.items()):
            lines.append(base + "\t" + ",".join(sorted(forms)))
        (OUT / "inflect_reverse" / f"ireverse_{shard}.txt").write_text(
            "\n".join(lines) + "\n", encoding="utf-8"
        )

    for shard, shard_rows in sorted(entry_shards.items()):
        lines = []
        for entry_id, row in shard_rows:
            lines.append(
                "\t".join(
                    [
                        str(entry_id),
                        row["word"],
                        row["phonetic"],
                        row["translation"],
                        row["tag"],
                    ]
                )
            )
        (OUT / "entries" / f"entry_{shard}.txt").write_text("\n".join(lines) + "\n", encoding="utf-8")

    zh_char_count = 0
    for bucket, chars in sorted(zh_index.items()):
        lines = []
        for char, entry_ids in sorted(chars.items()):
            lines.append(char + "\t" + ",".join(str(entry_id) for entry_id in entry_ids))
            zh_char_count += 1
        (OUT / "zh_index" / f"zh_{bucket}.txt").write_text("\n".join(lines) + "\n", encoding="utf-8")

    stats = {
        "source": str(SOURCE),
        "headwords": len(rows),
        "wordShards": len(word_shards),
        "inflectShards": len(inflect),
        "inflectReverseShards": len(reverse_inflect),
        "exchangeLinks": exchange_links,
        "wordFamilySource": word_family_stats["source"],
        "wordFamilySourceUrl": word_family_stats["sourceUrl"],
        "wordFamilyAvailable": word_family_stats["available"],
        "wordFamilyRows": word_family_stats["rows"],
        "wordFamilyMatchedRows": word_family_stats["matchedRows"],
        "wordFamilyCandidateLinks": word_family_stats["candidateLinks"],
        "wordFamilyMatchedLinks": word_family_stats["matchedLinks"],
        "wordFamilyLinksAdded": word_family_links_added,
        "ruleMatchedLinks": len(rule_links),
        "ruleLinksAdded": rule_links_added,
        "entryShards": len(entry_shards),
        "entryShardSize": ENTRY_SHARD_SIZE,
        "zhBuckets": len(zh_index),
        "zhChars": zh_char_count,
        "resultLimit": 20,
    }
    (OUT / "meta.json").write_text(json.dumps(stats, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(stats, ensure_ascii=False))


if __name__ == "__main__":
    main()
