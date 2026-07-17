"""Validate generated dictionary semantics across legacy and compact schemas."""

from __future__ import annotations

import argparse
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


def decode_delta_base36(value: str) -> list[int]:
    """Decode comma-separated base36 deltas (with optional RLE ^N suffix), rejecting malformed input."""
    if not value:
        raise DictionaryValidationError("delta-base36 list must not be empty")
    result: list[int] = []
    current = 0
    for token in value.split(","):
        # Check for RLE: value^count
        if "^" in token:
            if not re.match(r"^[0-9a-z]+\^[0-9]+$", token):
                raise DictionaryValidationError(f"invalid RLE token: {token!r}")
            val_str, count_str = token.split("^", 1)
            repeat = int(count_str)
            if repeat < 2 or repeat > 200:
                raise DictionaryValidationError(f"RLE count out of range: {token!r}")
            delta = int(val_str, 36)
            for _ in range(repeat):
                current += delta
                if result and current <= result[-1]:
                    raise DictionaryValidationError("decoded IDs must be strictly increasing")
                result.append(current)
        else:
            if not BASE36_TOKEN.fullmatch(token):
                raise DictionaryValidationError(f"invalid delta-base36 token: {token!r}")
            delta = int(token, 36)
            current += delta
            if result and current <= result[-1]:
                raise DictionaryValidationError("decoded IDs must be strictly increasing")
            result.append(current)
    return result


def decode_legacy_ids(value: str) -> list[int]:
    """Decode the pre-compaction decimal ID list."""
    return [int(token) for token in value.split(",")]


def read_tab_rows(path: Path) -> list[list[str]]:
    """Read non-empty tab-separated rows."""
    return [line.split("\t") for line in path.read_text(encoding="utf-8").splitlines() if line]


def read_entries() -> tuple[dict[int, tuple[str, str, str, str]], set[int]]:
    """Load canonical full entries keyed by entry ID (compact-v2: implicit eid, 3-4 fields)."""
    entries: dict[int, tuple[str, str, str, str]] = {}
    for path in sorted((DICT_DIR / "entries").glob("entry_*.txt")):
        shard = int(path.stem.split("_")[-1])
        base_id = shard * 500
        for line_idx, parts in enumerate(read_tab_rows(path)):
            if len(parts) not in (3, 4):
                raise DictionaryValidationError(f"invalid entry row in {path.name}: {parts!r}")
            entry_id = base_id + line_idx
            word, pron, trans = parts[0], parts[1], parts[2]
            tag = parts[3] if len(parts) >= 4 else ""
            entries[entry_id] = (word, pron, trans, tag)
    return entries, set(entries)


def decode_word_prefix(parts: list[str], prev_word: str) -> str:
    """Decode prefix-encoded word field. '3,ing' + prev='hunt' → 'hunting'."""
    raw = parts[0]
    if "," in raw:
        cnt_str, suffix = raw.split(",", 1)
        cnt = int(cnt_str)
        return prev_word[:cnt] + suffix
    return raw


def read_words(entries: dict[int, tuple[str, str, str, str]]) -> dict[str, int]:
    """Load compact word-to-entry mappings (compact-v2: prefix-encoded words, base36 eids)."""
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

    compact-v2: cn_index uses prefix encoding for phrases.
    """
    decoder = decode_delta_base36 if compact else decode_legacy_ids
    mappings: dict[str, tuple[int, ...]] = {}
    link_count = 0
    for path in sorted((DICT_DIR / directory).glob(f"{prefix}_*.txt")):
        prev_phrase = ""
        for parts in read_tab_rows(path):
            if len(parts) != 2:
                raise DictionaryValidationError(f"invalid index row in {path.name}: {parts!r}")
            # Decode prefix-encoded phrase (cn_index only)
            phrase = parts[0]
            if "," in phrase:
                p = phrase.split(",", 1)
                cnt = int(p[0])
                phrase = prev_phrase[:cnt] + (p[1] or "")
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


def read_links(directory: str, prefix: str) -> dict[str, tuple[str, ...]]:
    """Load word-based inflection relationships (excludes _eid shards)."""
    return {
        parts[0]: tuple(parts[1].split(","))
        for path in sorted((DICT_DIR / directory).glob(f"{prefix}_*.txt"))
        if "_eid_" not in path.name
        for parts in read_tab_rows(path)
    }


def validate(*, require_compact: bool) -> SemanticCounts:
    """Validate counts, ID sets, representative mappings, and schema metadata."""
    entries, entry_ids = read_entries()
    words = read_words(entries)
    compact = bool(list((DICT_DIR / "words").glob("word_*.txt")))
    cn_index, cn_links = read_index("cn_index", "cn", compact=compact)
    zh_index, zh_links = read_index("zh_index", "zh", compact=compact)
    inflect = read_links("inflect", "inflect")
    reverse_inflect = read_links("inflect_reverse", "ireverse")
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
            (meta.get("schema") == "compact-v2", "compact schema marker changed"),
            (
                meta.get("wordIndexFormat") == "prefixLen,suffix\\tbase36EntryId\\ttagCode(hex)",
                "word index format changed",
            ),
            (meta.get("chineseIdEncoding") == "delta-base36", "Chinese ID encoding changed"),
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
