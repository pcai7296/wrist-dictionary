import csv
import json
import re
import shutil
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "data" / "ecdict_tagged_14942_compact.csv"
OUT = ROOT / "src" / "common" / "dict"
ENTRY_SHARD_SIZE = 500
ZH_BUCKET_COUNT = 64


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

    word_shards = {}
    first_index = {}
    inflect = {}
    entry_shards = {}
    zh_index = {}
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

        for form in parse_exchange(row["exchange"]):
            form_key = key_for(form)
            inflect.setdefault(form_key, {}).setdefault(form.lower(), set()).add(row["word"])

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
        "entryShards": len(entry_shards),
        "entryShardSize": ENTRY_SHARD_SIZE,
        "zhBuckets": len(zh_index),
        "zhChars": zh_char_count,
cv        "resultLimit": 20,
    }
    (OUT / "meta.json").write_text(json.dumps(stats, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(stats, ensure_ascii=False))


if __name__ == "__main__":
    main()
