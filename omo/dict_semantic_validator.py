"""Validate generated dictionary semantics across legacy and compact schemas."""

from __future__ import annotations

import argparse
import base64
import json
import re
from dataclasses import asdict, dataclass
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DICT_DIR = ROOT / "src" / "common" / "dict"
EXPECTED_HEADWORDS = 14_942
EXPECTED_CN_PHRASES = 122_067
EXPECTED_CN_LINKS = 324_516
EXPECTED_ZH_CHARS = 3_731
EXPECTED_ZH_LINKS = 135_638
EXPECTED_INFLECT_LINKS = 26_225
EXPECTED_REVERSE_INFLECT_LINKS = 26_225
BASE36_TOKEN = re.compile(r"^[0-9a-z]+$")
BASE64URL_TOKEN = re.compile(r"^[A-Za-z0-9_-]+$")


class DictionaryValidationError(ValueError):
    """Raised when a generated dictionary row violates its schema."""


@dataclass(frozen=True, slots=True)
class SemanticCounts:
    headwords: int
    entry_ids: int
    cn_phrases: int
    cn_links: int
    zh_chars: int
    zh_links: int
    inflect_links: int
    reverse_inflect_links: int


def decode_delta_base64(value: str) -> list[int]:
    """Decode compact-v3 unpadded URL-safe Base64 ULEB128 deltas."""
    if not value or not BASE64URL_TOKEN.fullmatch(value):
        raise DictionaryValidationError("invalid Base64 ID list")
    try:
        payload = base64.b64decode(value + "=" * (-len(value) % 4), altchars=b"-_", validate=True)
    except (ValueError, base64.binascii.Error) as exc:
        raise DictionaryValidationError("invalid Base64 ID list") from exc
    result: list[int] = []
    current = 0
    delta = 0
    shift = 0
    for byte in payload:
        if shift > 28:
            raise DictionaryValidationError("ULEB128 value exceeds 32 bits")
        delta |= (byte & 0x7F) << shift
        if byte & 0x80:
            shift += 7
            continue
        current += delta
        if result and current <= result[-1]:
            raise DictionaryValidationError("decoded IDs must be strictly increasing")
        result.append(current)
        delta = 0
        shift = 0
    if shift or not result:
        raise DictionaryValidationError("truncated or empty ULEB128 ID list")
    return result


decode_delta_base36 = decode_delta_base64


def decode_prefix_field(raw: str, previous: str) -> str:
    """Decode a compact-v3 one-character Base36 front-coded field."""
    if not raw or raw[0] not in "0123456789abcdefghijklmnopqrstuvwxyz":
        raise DictionaryValidationError(f"invalid front-coded field: {raw!r}")
    prefix_len = int(raw[0], 36)
    if prefix_len > len(previous):
        raise DictionaryValidationError("front-code prefix exceeds previous value")
    return previous[:prefix_len] + raw[1:]


def decode_legacy_ids(value: str) -> list[int]:
    """Decode the pre-compaction decimal ID list."""
    return [int(token) for token in value.split(",")]


def read_tab_rows(path: Path) -> list[list[str]]:
    """Read non-empty tab-separated rows."""
    return [line.split("\t") for line in path.read_text(encoding="utf-8").splitlines() if line]


def read_entries() -> tuple[dict[int, tuple[str, str, str, str]], set[int]]:
    """Load compact-v3 front-coded canonical entries keyed by implicit entry ID."""
    entries: dict[int, tuple[str, str, str, str]] = {}
    for path in sorted((DICT_DIR / "entries").glob("entry_*.txt")):
        shard = int(path.stem.split("_")[-1])
        base_id = shard * 500
        previous_word = ""
        for line_idx, parts in enumerate(read_tab_rows(path)):
            if len(parts) not in (3, 4):
                raise DictionaryValidationError(f"invalid entry row in {path.name}: {parts!r}")
            entry_id = base_id + line_idx
            word = decode_prefix_field(parts[0], previous_word)
            previous_word = word
            pron, trans = parts[1], parts[2]
            tag = parts[3] if len(parts) >= 4 else ""
            entries[entry_id] = (word, pron, trans, tag)
    return entries, set(entries)


def decode_word_prefix(parts: list[str], prev_word: str) -> str:
    """Decode compact-v3 front-coded word field."""
    return decode_prefix_field(parts[0], prev_word)


def read_words(entries: dict[int, tuple[str, str, str, str]]) -> dict[str, int]:
    """Load compact-v3 word-to-entry mappings."""
    compact_paths = sorted((DICT_DIR / "words").glob("word_*.txt"))
    words: dict[str, int] = {}
    for path in compact_paths:
        prev_word = ""
        for parts in read_tab_rows(path):
            if len(parts) != 3:
                raise DictionaryValidationError(
                    f"invalid compact word row in {path.name}: {parts!r}"
                )
            word = decode_word_prefix(parts, prev_word)
            prev_word = word
            entry_id = int(parts[1], 36)  # base36
            if entry_id not in entries:
                raise DictionaryValidationError(f"unknown compact entry ID: {entry_id}")
            decoded_entry_word = entries[entry_id][0]
            if decoded_entry_word != word or entries[entry_id][3] != parts[2]:
                raise DictionaryValidationError(
                    f"compact word row disagrees with entry {entry_id}: "
                    f"word {word!r} != {decoded_entry_word!r} or "
                    f"tag {parts[2]!r} != {entries[entry_id][3]!r}"
                )
            words[word.lower()] = entry_id
    return words


def read_index(directory: str, prefix: str, *, compact: bool) -> tuple[dict[str, tuple[int, ...]], int]:
    """Load a Chinese index and return mappings plus link count.

    compact-v3: cn_index uses front-coded phrases and both indexes use Base64 ULEB128 IDs.
    """
    decoder = decode_delta_base64 if compact else decode_legacy_ids
    mappings: dict[str, tuple[int, ...]] = {}
    link_count = 0
    for path in sorted((DICT_DIR / directory).glob(f"{prefix}_*.txt")):
        prev_phrase = ""
        for parts in read_tab_rows(path):
            if len(parts) != 2:
                raise DictionaryValidationError(f"invalid index row in {path.name}: {parts!r}")
            # Decode prefix-encoded phrase (cn_index only)
            phrase = parts[0]
            if directory == "cn_index":
                phrase = decode_prefix_field(phrase, prev_phrase)
            ids = tuple(decoder(parts[1]))
            mappings[phrase] = ids
            link_count += len(ids)
            prev_phrase = phrase
    return mappings, link_count


def count_links(directory: str, prefix: str) -> int:
    """Count total inflection links across all shard files (handles _eid duplicates)."""
    total = 0
    for path in sorted((DICT_DIR / directory).glob(f"{prefix}_*.txt")):
        for parts in read_tab_rows(path):
            total += len(parts[1].split(","))
    return total


def read_links(
    directory: str,
    prefix: str,
    entries: dict[int, tuple[str, str, str, str]],
) -> dict[str, tuple[str, ...]]:
    """Load compact-v3 front-coded inflection relationships as words."""
    links: dict[str, tuple[str, ...]] = {}
    for path in sorted((DICT_DIR / directory).glob(f"{prefix}_*.txt")):
        previous = ""
        for parts in read_tab_rows(path):
            if len(parts) != 2:
                raise DictionaryValidationError(f"invalid inflection row in {path.name}: {parts!r}")
            key = decode_prefix_field(parts[0], previous)
            previous = key
            values: list[str] = []
            for value in parts[1].split(","):
                if value.startswith("@"):
                    entry_id = int(value[1:], 36)
                    if entry_id not in entries:
                        raise DictionaryValidationError(f"unknown inflection entry ID: {entry_id}")
                    values.append(entries[entry_id][0])
                elif directory == "inflect":
                    entry_id = int(value, 36)
                    if entry_id not in entries:
                        raise DictionaryValidationError(f"unknown inflection entry ID: {entry_id}")
                    values.append(entries[entry_id][0])
                else:
                    values.append(value)
            links[key] = tuple(values)
    return links


def validate(*, require_compact: bool) -> SemanticCounts:
    """Validate counts, ID sets, representative mappings, and schema metadata."""
    entries, entry_ids = read_entries()
    words = read_words(entries)
    compact = bool(list((DICT_DIR / "words").glob("word_*.txt")))
    cn_index, cn_links = read_index("cn_index", "cn", compact=compact)
    zh_index, zh_links = read_index("zh_index", "zh", compact=compact)
    inflect = read_links("inflect", "inflect", entries)
    reverse_inflect = read_links("inflect_reverse", "ireverse", entries)
    inflect_links = count_links("inflect", "inflect")
    reverse_links = count_links("inflect_reverse", "ireverse")

    checks = (
        (len(entries) == EXPECTED_HEADWORDS, "canonical entry count changed"),
        (len(words) == EXPECTED_HEADWORDS, "compact headword count changed"),
        (len(cn_index) == EXPECTED_CN_PHRASES, "Chinese phrase count changed"),
        (cn_links == EXPECTED_CN_LINKS, "Chinese phrase link count changed"),
        (len(zh_index) == EXPECTED_ZH_CHARS, "Chinese character count changed"),
        (zh_links == EXPECTED_ZH_LINKS, "Chinese character link count changed"),
        (inflect_links == EXPECTED_INFLECT_LINKS, "inflection link count changed"),
        (
            reverse_links == EXPECTED_REVERSE_INFLECT_LINKS,
            "reverse inflection link count changed",
        ),
        (set(words.values()) == entry_ids, "compact word IDs differ from canonical entries"),
        (
            all(set(ids) <= entry_ids for ids in cn_index.values()),
            "Chinese phrase index contains unknown entry IDs",
        ),
        (
            all(set(ids) <= entry_ids for ids in zh_index.values()),
            "Chinese character index contains unknown entry IDs",
        ),
        (words.get("ability") == 21, "representative English mapping changed"),
        (entries.get(0, ("", "", "", ""))[0] == "a", "first canonical entry changed"),
        (21 in cn_index.get("能力", ()), "representative Chinese phrase mapping changed"),
        (21 in zh_index.get("能", ()), "representative Chinese character mapping changed"),
        ("ability" in inflect.get("abilities", ()), "representative inflection changed"),
        (
            "abilities" in reverse_inflect.get("ability", ()),
            "representative reverse inflection changed",
        ),
    )
    for valid, message in checks:
        if not valid:
            raise DictionaryValidationError(message)

    meta = json.loads((DICT_DIR / "meta.json").read_text(encoding="utf-8"))
    expected_meta = {
        "headwords": EXPECTED_HEADWORDS,
        "wordIndexEntries": EXPECTED_HEADWORDS,
        "cnIndexPhrases": EXPECTED_CN_PHRASES,
        "cnIndexLinks": EXPECTED_CN_LINKS,
        "zhChars": EXPECTED_ZH_CHARS,
        "zhIndexLinks": EXPECTED_ZH_LINKS,
        "inflectLinks": EXPECTED_INFLECT_LINKS,
        "inflectReverseLinks": EXPECTED_REVERSE_INFLECT_LINKS,
    }
    for key, expected in expected_meta.items():
        if meta.get(key) != expected:
            raise DictionaryValidationError(f"metadata {key} differs from trusted baseline")
    if require_compact:
        compact_checks = (
            (compact, "compact word index is missing"),
            (len(list((DICT_DIR / "words").glob("word_*.txt"))) == 26, "word shard count changed"),
            (meta.get("schema") == "compact-v3", "compact schema marker changed"),
            (
                meta.get("wordIndexFormat") == "base36PrefixLen+suffix\\tbase36EntryId\\ttagCode(hex)",
                "word index format changed",
            ),
            (meta.get("chineseIdEncoding") == "base64url-uleb128-delta", "Chinese ID encoding changed"),
            (len(list((DICT_DIR / "cn_index").glob("cn_*.txt"))) == 96, "cn bucket count changed"),
            (len(list((DICT_DIR / "zh_index").glob("zh_*.txt"))) == 64, "zh bucket count changed"),
            (len(list((DICT_DIR / "inflect").glob("inflect_*.txt"))) == 26, "inflect shard count changed"),
            (len(list((DICT_DIR / "inflect_reverse").glob("ireverse_*.txt"))) == 26, "reverse inflect shard count changed"),
        )
        for valid, message in compact_checks:
            if not valid:
                raise DictionaryValidationError(message)

    return SemanticCounts(
        headwords=len(words),
        entry_ids=len(entry_ids),
        cn_phrases=len(cn_index),
        cn_links=cn_links,
        zh_chars=len(zh_index),
        zh_links=zh_links,
        inflect_links=inflect_links,
        reverse_inflect_links=reverse_links,
    )


def main() -> None:
    """Run the semantic validator from the command line."""
    parser = argparse.ArgumentParser()
    parser.add_argument("--require-compact", action="store_true")
    args = parser.parse_args()
    counts = validate(require_compact=args.require_compact)
    print(json.dumps(asdict(counts), ensure_ascii=False, sort_keys=True))


if __name__ == "__main__":
    main()
