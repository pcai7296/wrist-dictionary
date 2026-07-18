# noqa: SIZE_OK - existing generator is intentionally a single deterministic pipeline.
import csv
import base64
import gzip
import json
import os
import re
import shutil
import xml.etree.ElementTree as ET
from zipfile import ZipFile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "data" / "ecdict_tagged_14942_compact.csv"
WORD_FAMILY_SOURCE = ROOT / "data" / "bnc_coca_word_family_lists_v2.xlsx"
WORD_FAMILY_SOURCE_URL = "https://www.eapfoundation.com/vocab/general/bnccoca/"
CCEDICT_SOURCE = ROOT / "data" / "cedict.txt.gz"
CCEDICT_URL = "https://www.mdbg.net/chinese/export/cedict/cedict_1_0_ts_utf-8_mdbg.txt.gz"
WORDNET_DIR = ROOT / "data" / "dict"
WORDNET_FILES = {"n": "data.noun", "v": "data.verb", "a": "data.adj", "r": "data.adv"}
WORDNET_VALID_POS = {"n", "v", "a", "r"}
OUT = ROOT / "src" / "common" / "dict"
ENTRY_SHARD_SIZE = 500
CN_BUCKET_COUNT = 96
ZH_BUCKET_COUNT = 64
XLSX_NS = {"a": "http://schemas.openxmlformats.org/spreadsheetml/2006/main"}
BASE36_DIGITS = "0123456789abcdefghijklmnopqrstuvwxyz"
BASE36_TOKEN = re.compile(r"^[0-9a-z]+$")


class DictionaryFormatError(ValueError):
    """Raised when compact dictionary data violates its wire contract."""


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


TAG_TO_CODE = {
    "zk": "z", "gk": "g", "cet4": "4", "cet6": "6",
    "ky": "k", "toefl": "t", "ielts": "i", "gre": "e",
}

TAG_TO_BIT = {'z': 1, 'g': 2, '4': 4, '6': 8, 'k': 16, 'i': 32, 't': 64, 'e': 128}

IPA_MAP = {
    '\u0259': 'a',   # ə schwa
    '\u04d9': 'a',   # ә cyrillic schwa (data variant)
    '\u025a': 'r',   # ɚ rhotic schwa
    '\u0454': 'e',   # є cyrillian ie
    '\u03b5': 'e',   # ε greek epsilon
    '\u026a': 'i',   # ɪ small cap i
    '\u02c8': "'",   # ˈ primary stress
    '\u02cc': ',',   # ˌ secondary stress
    '\u0251': 'A',   # ɑ script a
    '\u028a': 'U',   # ʊ
    '\u0283': 'S',   # ʃ esh
    '\u0292': 'Z',   # ʒ ezh
    '\u03b8': 'T',   # θ theta
    '\u00f0': 'D',   # ð eth
    '\u014b': 'N',   # ŋ eng
    '\u0254': 'O',   # ɔ open o
    '\u00e6': 'E',   # æ ash
    '\u025b': 'e',   # ɛ epsilon
    '\u025c': 'R',   # ɜ reversed epsilon
    '\u02d0': '|',   # ː length mark
    '\u0252': 'Q',   # ɒ turned script a
    '\u028c': 'V',   # ʌ turned v
    '\u0261': 'g',   # ɡ script g
}

PHRASE_ENCODE = {
    'vt. ': '!',
    'vi. ': '$',
    'n. ': '@',
    'a. ': '#',
    'ad. ': '%',
    'adv. ': '%',
    'prep. ': '^',
    'conj. ': '&',
    'pron. ': '*',
    'int. ': '(',
    'num. ': ')',
    'art. ': '-',
    'aux. ': '=',
    '[计]': '{',
    '[法]': '}',
    '[医]': '|',
    '[生]': '[',
    '[化]': ']',
    '[物]': '<',
    '[经]': '>',
}


def compact_tag(value):
    """Compress space-separated tags into comma-separated single-char codes.
    'cet4 cet6 ky toefl ielts gre' -> '4,6,k,t,i,e'
    """
    if not value:
        return value
    codes = []
    for tag in value.split():
        code = TAG_TO_CODE.get(tag)
        if code:
            codes.append(code)
    return ",".join(codes)


def encode_tag_bitmap(value):
    """Convert comma-separated tag codes to a hex bitmask.
    'g,4,6,k,t,e' -> '5f'
    Returns empty string if no tags.
    """
    if not value:
        return ""
    mask = 0
    for code in value.split(","):
        code = code.strip()
        if code in TAG_TO_BIT:
            mask |= TAG_TO_BIT[code]
    return "" if mask == 0 else format(mask, 'x')


def encode_phrase_dict(value):
    """Replace common POS/domain markers with single-char codes."""
    if not value:
        return value
    result = value
    for pattern, code in sorted(PHRASE_ENCODE.items(), key=lambda x: -len(x[0])):
        result = result.replace(pattern, code)
    return result


def normalize_chinese(value):
    return "".join(re.findall(r"[\u4e00-\u9fff]", value or ""))


def write_txt(path, content):
    """Write text file with LF line endings (not platform-native CRLF)."""
    with open(path, "w", encoding="utf-8", newline="\n") as f:
        f.write(content)


# CC-CEDICT English stop words — words too generic to form useful zh→en mappings
CC_STOP_WORDS = {
    "the", "this", "that", "these", "those", "a", "an", "is", "are",
    "was", "were", "be", "been", "being", "have", "has", "had",
    "do", "does", "did", "will", "would", "can", "could", "may", "might",
    "shall", "should", "to", "of", "in", "on", "at", "for", "with",
    "by", "from", "as", "but", "or", "and", "not", "no", "nor",
    "it", "its", "he", "him", "she", "her", "they", "them", "we", "us",
    "you", "your", "my", "me", "our", "all", "each", "every", "some",
    "any", "one", "two", "etc", "ie", "eg", "vs", "aka", "vs",
    "cl", "lit", "fig", "coll", "slang", "arch", "dial", "old",
    "x", "etc", "de", "en", "la", "le", "el",
}


def load_cc_cedict(path):
    """Parse CC-CEDICT, return dict: simplified Chinese phrase → [English meanings]"""
    if not path.exists():
        print(f"  [CC-CEDICT] 文件不存在: {path}")
        print(f"  [CC-CEDICT] 请下载: {CCEDICT_URL}")
        print(f"  [CC-CEDICT] 保存到: {path}")
        return {}

    result = {}
    with gzip.open(str(path), "rt", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#"):
                continue

            # Parse: Traditional Simplified [pin1 yin1] /meaning1/meaning2/
            bracket = line.find("[")
            slash = line.find("/")
            if bracket < 0 or slash < 0:
                continue

            chinese_part = line[:bracket].strip()
            trad_simp = chinese_part.split()
            if len(trad_simp) < 2:
                continue

            simplified = trad_simp[1]
            cn_chars = "".join(re.findall(r"[\u4e00-\u9fff]+", simplified))
            if len(cn_chars) < 2:
                continue

            # Extract English meanings
            english_text = line[slash:]  # /meaning1/meaning2/
            meanings = [
                m.strip() for m in english_text.split("/") if m.strip()
            ]

            if cn_chars in result:
                result[cn_chars].extend(meanings)
            else:
                result[cn_chars] = meanings

    return result


def zh_bucket_for(char):
    return f"{ord(char) % ZH_BUCKET_COUNT:02x}"


def cn_bucket_for(char):
    return f"{ord(char) % CN_BUCKET_COUNT:02x}"


def entry_shard_for(entry_id):
    return f"{entry_id // ENTRY_SHARD_SIZE:02d}"


def to_base36(value):
    if value < 0:
        raise DictionaryFormatError("base36 value must be non-negative")
    if value == 0:
        return "0"
    digits = []
    while value:
        value, remainder = divmod(value, 36)
        digits.append(BASE36_DIGITS[remainder])
    return "".join(reversed(digits))


def encode_uleb128(value):
    if value < 0:
        raise DictionaryFormatError("ULEB128 value must be non-negative")
    encoded = bytearray()
    while True:
        byte = value & 0x7F
        value >>= 7
        encoded.append(byte | (0x80 if value else 0))
        if not value:
            return bytes(encoded)


def encode_delta_ids(entry_ids):
    previous = 0
    encoded = bytearray()
    for position, entry_id in enumerate(entry_ids):
        if entry_id < 0:
            raise DictionaryFormatError("entry IDs must be non-negative")
        if position and entry_id <= previous:
            raise DictionaryFormatError("entry IDs must be strictly increasing")
        encoded.extend(encode_uleb128(entry_id - previous))
        previous = entry_id
    if not encoded:
        raise DictionaryFormatError("entry ID list must not be empty")
    return base64.urlsafe_b64encode(bytes(encoded)).decode("ascii").rstrip("=")


def encode_rle(tokens):
    """Apply run-length encoding to a list of delta-base36 tokens.
    
    Consecutive identical tokens become 'value^count' (^ is not a valid base36 char).
    Example: ['1','1','1','2','3','3'] → ['1^3','2','3^2']
    """
    if not tokens:
        return ""
    result = []
    current = tokens[0]
    count = 1
    for t in tokens[1:]:
        if t == current:
            count += 1
        else:
            if count > 1:
                result.append(f"{current}^{count}")
            else:
                result.append(current)
            current = t
            count = 1
    if count > 1:
        result.append(f"{current}^{count}")
    else:
        result.append(current)
    return ",".join(result)


def encode_front_code(value, previous):
    prefix_len = 0
    limit = min(len(value), len(previous))
    while prefix_len < limit and value[prefix_len] == previous[prefix_len]:
        prefix_len += 1
    if prefix_len >= 36:
        raise DictionaryFormatError("front-code prefix exceeds one Base36 character")
    return BASE36_DIGITS[prefix_len] + value[prefix_len:]


def decode_front_code(value, previous):
    if not value or value[0] not in BASE36_DIGITS:
        raise DictionaryFormatError(f"invalid front-coded field: {value!r}")
    prefix_len = int(value[0], 36)
    if prefix_len > len(previous):
        raise DictionaryFormatError("front-code prefix exceeds previous value")
    return previous[:prefix_len] + value[1:]


def decode_delta_ids(value):
    if not value or not re.fullmatch(r"[A-Za-z0-9_-]+", value):
        raise DictionaryFormatError("invalid Base64 ID list")
    try:
        raw = base64.b64decode(value + "=" * (-len(value) % 4), altchars=b"-_", validate=True)
    except (ValueError, base64.binascii.Error) as exc:
        raise DictionaryFormatError("invalid Base64 ID list") from exc
    if not raw:
        raise DictionaryFormatError("Base64 ID list must not be empty")
    result = []
    current = 0
    delta = 0
    shift = 0
    for byte in raw:
        payload = byte & 0x7F
        if shift >= 64 or (shift == 63 and payload > 1):
            raise DictionaryFormatError("ULEB128 value exceeds 64 bits")
        delta |= payload << shift
        if byte & 0x80:
            shift += 7
            if shift >= 64:
                raise DictionaryFormatError("ULEB128 value exceeds 64 bits")
            continue
        current += delta
        if result and current <= result[-1]:
            raise DictionaryFormatError("decoded IDs must be strictly increasing")
        result.append(current)
        delta = 0
        shift = 0
    if shift != 0:
        raise DictionaryFormatError("truncated ULEB128 value")
    return result


# Compatibility names for existing offline callers; compact-v3 is the wire format.
encode_delta_base64 = encode_delta_ids
encode_delta_base36 = encode_delta_ids
decode_delta_base36 = decode_delta_ids
decode_delta_base64 = decode_delta_ids


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


def load_wordnet_derived_links(word_set):
    """Load derivationally related forms from WordNet data files (+ pointers).

    Returns dict with stats and list of (form, base) links.
    """
    stats = {
        "available": WORDNET_DIR.exists(),
        "source": str(WORDNET_DIR),
        "totalLinks": 0,
        "matchedLinks": 0,
        "links": [],
    }
    if not WORDNET_DIR.exists():
        return stats

    # Build offset -> lemmas from data files, and collect + pointer links
    all_links = set()

    for pos_code, filename in WORDNET_FILES.items():
        filepath = WORDNET_DIR / filename
        if not filepath.exists():
            continue

        offset_to_lemmas = {}
        with open(filepath, "r", encoding="utf-8", errors="replace") as f:
            for line in f:
                line = line.rstrip("\n\r")
                if not line or not re.match(r"^\d{8}\s", line):
                    continue
                pipe_pos = line.find("|")
                if pipe_pos < 0:
                    continue
                parts = line[:pipe_pos].rstrip().split()
                if len(parts) < 7:
                    continue
                offset = parts[0]
                try:
                    nwords = int(parts[3])
                except ValueError:
                    continue
                lemmas = []
                for i in range(nwords):
                    idx = 4 + 2 * i
                    if idx < len(parts):
                        lemmas.append(parts[idx])
                offset_to_lemmas[offset] = lemmas
                nptr_idx = 4 + 2 * nwords
                if nptr_idx >= len(parts):
                    continue
                try:
                    nptr = int(parts[nptr_idx])
                except ValueError:
                    continue
                ptr_idx = nptr_idx + 1
                for _ in range(nptr):
                    if ptr_idx + 2 >= len(parts):
                        break
                    ptr_symbol = parts[ptr_idx]
                    ptr_offset = parts[ptr_idx + 1]
                    ptr_pos = parts[ptr_idx + 2]
                    ptr_idx += 4
                    if ptr_symbol == "+" and ptr_pos in WORDNET_VALID_POS:
                        for lemma in lemmas:
                            target_lemmas = offset_to_lemmas.get(ptr_offset, [])
                            for tl in target_lemmas:
                                if tl.lower() != lemma.lower():
                                    all_links.add((tl.lower(), lemma.lower()))

    stats["totalLinks"] = len(all_links)
    matched = []
    for form, base in all_links:
        if form in word_set and base in word_set and form != base:
            matched.append((form, base))
    stats["matchedLinks"] = len(matched)
    stats["links"] = sorted(matched)
    return stats


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
    (OUT / "cn_index").mkdir(parents=True)

    word_indexes = {letter: [] for letter in "abcdefghijklmnopqrstuvwxyz"}
    inflect = {}
    reverse_inflect = {}

    entry_shards = {}
    zh_index = {}
    word_set = {row["word"].lower() for row in rows}
    word_to_entry = {row["word"].lower(): entry_id for entry_id, row in enumerate(rows)}
    word_phonetics = {row["word"].lower(): row["phonetic"] for row in rows if row["phonetic"]}
    exchange_links = 0
    word_family_links_added = 0

    def add_inflect_link(form, base):
        form = normalize_family_word(form)
        base = normalize_family_word(base)
        if not form or not base or form == base:
            return False
        form_key = form[0]
        rev_key = base[0]
        before = len(inflect.setdefault(form_key, {}).setdefault(form, set()))
        inflect[form_key][form].add(base)
        reverse_inflect.setdefault(rev_key, {}).setdefault(base, set()).add(form)
        return len(inflect[form_key][form]) > before

    for entry_id, row in enumerate(rows):
        first_letter = row["word"].lower()[0]
        word_indexes[first_letter].append((entry_id, row))
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

    wordnet_stats = load_wordnet_derived_links(word_set)
    wordnet_links_added = 0
    for form, base in wordnet_stats["links"]:
        if add_inflect_link(form, base):
            wordnet_links_added += 1

    for first_letter, indexed_rows in sorted(word_indexes.items()):
        indexed_rows.sort(key=lambda item: item[1]["word"].lower())
        lines = []
        prev_word = ""
        for entry_id, row in indexed_rows:
            word = row["word"]
            lines.append(
                "\t".join(
                    [
                        encode_front_code(word, prev_word),
                        to_base36(entry_id),
                        encode_tag_bitmap(compact_tag(row["tag"])),
                    ]
                )
            )
            prev_word = word
        write_txt(OUT / "words" / f"word_{first_letter}.txt", 
            "\n".join(lines) + "\n"
        )

    inflect_rows = []
    for forms in inflect.values():
        for form, bases in forms.items():
            encoded_bases = []
            for base in sorted(bases):
                entry_id = word_to_entry.get(base)
                if entry_id is None:
                    raise DictionaryFormatError(f"inflection base is not a canonical entry: {base}")
                encoded_bases.append(to_base36(entry_id))
            inflect_rows.append((form, ",".join(encoded_bases)))
    for initial in "abcdefghijklmnopqrstuvwxyz":
        lines = []
        previous = ""
        for form, values in sorted(row for row in inflect_rows if row[0][0] == initial):
            lines.append(encode_front_code(form, previous) + "\t" + values)
            previous = form
        write_txt(OUT / "inflect" / f"inflect_{initial}.txt", "\n".join(lines) + "\n")

    reverse_rows = []
    for bases in reverse_inflect.values():
        for base, forms in bases.items():
            values = []
            for form in sorted(forms):
                entry_id = word_to_entry.get(form)
                values.append("@" + to_base36(entry_id) if entry_id is not None else form)
            reverse_rows.append((base, ",".join(values)))
    for initial in "abcdefghijklmnopqrstuvwxyz":
        lines = []
        previous = ""
        for base, values in sorted(row for row in reverse_rows if row[0][0] == initial):
            lines.append(encode_front_code(base, previous) + "\t" + values)
            previous = base
        write_txt(OUT / "inflect_reverse" / f"ireverse_{initial}.txt",
            "\n".join(lines) + "\n"
        )

    for shard, shard_rows in sorted(entry_shards.items()):
        lines = []
        previous_word = ""
        for entry_id, row in shard_rows:
            phonetic = row["phonetic"]
            # Inherit phonetic from base word when empty (e.g. regular inflections)
            if not phonetic and row["exchange"]:
                for form in parse_exchange(row["exchange"]):
                    if len(form) > 1 and form.lower() in word_phonetics:
                        phonetic = word_phonetics[form.lower()]
                        break
            fields = [
                encode_front_code(row["word"], previous_word),
                "".join(IPA_MAP.get(c, c) for c in phonetic),
                encode_phrase_dict(row["translation"]),
            ]
            tag_code = encode_tag_bitmap(compact_tag(row["tag"]))
            if tag_code:
                fields.append(tag_code)
            lines.append("\t".join(fields))
            previous_word = row["word"]
        write_txt(OUT / "entries" / f"entry_{shard}.txt", "\n".join(lines) + "\n")

    # Build cn_index: Chinese phrase → entry IDs (from ECDICT translations)
    cn_index = {}
    for entry_id, row in enumerate(rows):
        zh_text = normalize_chinese(row["translation"])
        # Clean: remove brackets content, English, digits
        cleaned = re.sub(r'\[.*?\]', '', row["translation"])
        cleaned = re.sub(r'[a-zA-Z0-9]', '', cleaned)
        # Split by common separators
        parts = re.split(r'[,，;；\s\r\n/\\\\]+', cleaned)
        for phrase in parts:
            phrase = phrase.strip()
            if len(phrase) >= 2 and bool(re.search(r'[\u4e00-\u9fff]', phrase)):
                bucket = cn_bucket_for(phrase[0])
                cn_index.setdefault(bucket, {}).setdefault(phrase, set()).add(entry_id)

    # Augment cn_index with CC-CEDICT (Chinese → English reverse lookup)
    ccedict = load_cc_cedict(CCEDICT_SOURCE)
    ccedict_added = 0
    if ccedict:
        # Build word → entry_id reverse map
        word_to_entry = {}
        for entry_id, row in enumerate(rows):
            word_lower = row["word"].lower()
            word_to_entry[word_lower] = entry_id

        ccedict_added = 0
        for phrase, meanings in ccedict.items():
            # Extract English content words from all meanings
            matched_ids = set()
            for meaning in meanings:
                # Remove CL: patterns and parentheticals
                cleaned = re.sub(r'CL:[^/]+', '', meaning)
                cleaned = re.sub(r'\([^)]*\)', '', cleaned)
                words = re.findall(r"[a-zA-Z]+", cleaned.lower())
                for w in words:
                    if len(w) >= 3 and w not in CC_STOP_WORDS and w in word_to_entry:
                        matched_ids.add(word_to_entry[w])

            if matched_ids:
                ccedict_added += 1
                bucket = cn_bucket_for(phrase[0])
                cn_index.setdefault(bucket, {}).setdefault(phrase, set()).update(matched_ids)

        print(f"  [CC-CEDICT] 已合并 {ccedict_added} 个中文词组")
    else:
        print("  [CC-CEDICT] 跳过（文件未找到）")

    cn_phrase_count = 0
    cn_link_count = 0
    for bucket_number in range(CN_BUCKET_COUNT):
        bucket = f"{bucket_number:02x}"
        lines = []
        prev_phrase = ""
        for phrase in sorted(cn_index.get(bucket, {})):
            ids = encode_delta_ids(sorted(cn_index[bucket][phrase]))
            lines.append(encode_front_code(phrase, prev_phrase) + "\t" + ids)
            cn_phrase_count += 1
            cn_link_count += len(cn_index[bucket][phrase])
            prev_phrase = phrase
        write_txt(OUT / "cn_index" / f"cn_{bucket}.txt", "\n".join(lines) + "\n")

    zh_char_count = 0
    zh_link_count = 0
    zh_rle_savings = 0
    for bucket_number in range(ZH_BUCKET_COUNT):
        bucket = f"{bucket_number:02x}"
        chars = zh_index.get(bucket, {})
        lines = []
        for char, entry_ids in sorted(chars.items()):
            encoded = encode_delta_ids(sorted(entry_ids))
            lines.append(char + "\t" + encoded)
            zh_char_count += 1
            zh_link_count += len(entry_ids)
        write_txt(OUT / "zh_index" / f"zh_{bucket}.txt", "\n".join(lines) + "\n")

    stats = {
        "source": str(SOURCE),
        "headwords": len(rows),
        "schema": "compact-v3",
        "wordIndexFormat": "base36PrefixLen+suffix\\tbase36EntryId\\ttagCode(hex)",
        "entriesFormat": "base36PrefixLen+wordSuffix\\tpron\\tdef\\t[tagCode]",
        "entriesEncoding": "implicit-eid, front-coded-word, ipa-mapped, phrase-encoded",
        "wordIndexFiles": len(word_indexes),
        "wordIndexEntries": len(rows),
        "wordShards": len(word_indexes),
        "chineseIdEncoding": "base64url-uleb128-delta",
        "chineseIdOrdering": "strictly-increasing",
        "inflectShards": len(inflect),
        "inflectReverseShards": len(reverse_inflect),
        "inflectLinks": sum(len(bases) for forms in inflect.values() for bases in forms.values()),
        "inflectReverseLinks": sum(
            len(forms) for bases in reverse_inflect.values() for forms in bases.values()
        ),
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
        "wordnetSource": wordnet_stats["source"],
        "wordnetAvailable": wordnet_stats["available"],
        "wordnetTotalLinks": wordnet_stats["totalLinks"],
        "wordnetMatchedLinks": wordnet_stats["matchedLinks"],
        "wordnetLinksAdded": wordnet_links_added,
        "entryShards": len(entry_shards),
        "entryShardSize": ENTRY_SHARD_SIZE,
        "cnIndexFormat": "base36PrefixLen+suffix\\tbase64url-uleb128-delta",
        "inflectFormat": "base36PrefixLen+form\\tbase36EntryIds",
        "reverseInflectFormat": "base36PrefixLen+base\\t@base36EntryId-or-raw",
        "zhIndexRLE": False,
        "zhIndexRLESavingsBytes": 0,
        "zhBuckets": ZH_BUCKET_COUNT,
        "zhChars": zh_char_count,
        "zhIndexLinks": zh_link_count,
        "cnIndexBuckets": CN_BUCKET_COUNT,
        "cnBucketCount": CN_BUCKET_COUNT,
        "zhBucketCount": ZH_BUCKET_COUNT,
        "cnIndexPhrases": cn_phrase_count,
        "cnIndexLinks": cn_link_count,
        "ccCedictSource": str(CCEDICT_SOURCE) if CCEDICT_SOURCE.exists() else "",
        "ccCedictMerged": ccedict_added,
        "resultLimit": 20,
    }
    write_txt(OUT / "meta.json", json.dumps(stats, ensure_ascii=False, indent=2))
    print(json.dumps(stats, ensure_ascii=False))


if __name__ == "__main__":
    main()
