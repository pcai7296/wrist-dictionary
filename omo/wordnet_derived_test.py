#!/usr/bin/env python3
"""Query WordNet for all derivationally related forms of 14k ECDICT words.

WordNet data file format (data.noun, data.verb, data.adj, data.adv):
  offset lex_id pos word_count word1 sense_num ... nptr pointer1 ... | gloss

Each pointer: ptr_symbol offset ptr_pos src_word_idx tgt_word_idx
The '+' pointer = derivationally related form.
"""

import csv
import re
from collections import defaultdict
from pathlib import Path

DATA_DIR = Path(__file__).resolve().parent.parent / "data"
DICT_DIR = DATA_DIR / "dict"
ECdict_CSV = DATA_DIR / "ecdict_tagged_14942_compact.csv"

POS_FILES = {"n": "data.noun", "v": "data.verb", "a": "data.adj", "r": "data.adv"}
POS_FULL = {"n": "noun", "v": "verb", "a": "adj", "r": "adv"}
VALID_POS = {"n", "v", "a", "r"}


def load_ecdict_words():
    words = set()
    with open(ECdict_CSV, "r", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            w = row.get("word", "").strip().lower()
            if w:
                words.add(w)
    return words


def parse_data_file(pos_code):
    """Parse WordNet data file, extract derivationally related forms (+ pointers).

    Returns: {source_lemma: set of target_lemma}
    """
    filename = POS_FILES.get(pos_code)
    if not filename:
        return {}
    filepath = DICT_DIR / filename
    if not filepath.exists():
        return {}

    # First pass: build offset -> lemmas mapping from the data file itself
    # (each synset lists its lemmas inline)
    offset_to_lemmas = {}
    derived = defaultdict(set)

    with open(filepath, "r", encoding="utf-8", errors="replace") as f:
        for line in f:
            line = line.rstrip("\n\r")
            if not line or not re.match(r"^\d{8}\s", line):
                continue

            # Split at the pipe to separate structured part from gloss
            pipe_pos = line.find("|")
            if pipe_pos < 0:
                continue
            structured = line[:pipe_pos].rstrip()

            parts = structured.split()
            if len(parts) < 7:
                continue

            offset = parts[0]
            # parts[1] = lex_file_id, parts[2] = pos
            try:
                nwords = int(parts[3])
            except ValueError:
                continue

            # Extract lemmas: parts[4], parts[6], parts[8], ... (every other)
            lemmas = []
            for i in range(nwords):
                idx = 4 + 2 * i
                if idx < len(parts):
                    lemmas.append(parts[idx])
            offset_to_lemmas[offset] = lemmas

            # Find nptr_idx: after words
            nptr_idx = 4 + 2 * nwords
            if nptr_idx >= len(parts):
                continue
            try:
                nptr = int(parts[nptr_idx])
            except ValueError:
                continue

            # Parse pointers starting at nptr_idx + 1
            ptr_idx = nptr_idx + 1
            for _ in range(nptr):
                if ptr_idx + 2 >= len(parts):
                    break
                ptr_symbol = parts[ptr_idx]
                ptr_offset = parts[ptr_idx + 1]
                ptr_pos = parts[ptr_idx + 2]
                # parts[ptr_idx + 3] would be src_tgt but we don't need it
                ptr_idx += 4

                if ptr_symbol == "+" and ptr_pos in VALID_POS:
                    # Derivationally related form
                    for lemma in lemmas:
                        target_lemmas = offset_to_lemmas.get(ptr_offset, [])
                        for tl in target_lemmas:
                            if tl.lower() != lemma.lower():
                                derived[lemma.lower()].add(tl.lower())

    return dict(derived)


def main():
    print("Loading 14k ECDICT words...")
    ecdict_words = load_ecdict_words()
    print(f"  Loaded {len(ecdict_words)} unique headwords")

    all_derived = defaultdict(set)

    for pos_code in ["n", "v", "a", "r"]:
        print(f"\nParsing data.{POS_FULL[pos_code]}...")
        result = parse_data_file(pos_code)
        print(f"  {len(result)} source lemmas with + pointers")
        for lemma, targets in result.items():
            all_derived[lemma].update(targets)

    print(f"\n{'='*60}")
    total_links = sum(len(v) for v in all_derived.values())
    print(f"Total derived form links (all WordNet): {total_links}")
    print(f"Unique source lemmas: {len(all_derived)}")

    # Filter: only 14k words as source
    ecdict_derived = {}
    for lemma in ecdict_words:
        if lemma in all_derived:
            ecdict_derived[lemma] = all_derived[lemma]

    # Collect all targets
    all_targets = set()
    for targets in ecdict_derived.values():
        all_targets.update(targets)

    new_words = all_targets - ecdict_words
    overlap = all_targets & ecdict_words

    total = sum(len(v) for v in ecdict_derived.values())
    print(f"\n{'='*60}")
    print(f"14k words with derived forms: {len(ecdict_derived)}/{len(ecdict_words)}")
    print(f"Total derived links from 14k: {total}")
    print(f"Unique derived targets: {len(all_targets)}")
    print(f"  Already in 14k: {len(overlap)}")
    print(f"  NEW (not in 14k): {len(new_words)}")

    # Sample
    print(f"\nSample:")
    count = 0
    for lemma in sorted(ecdict_derived.keys()):
        if count >= 20:
            break
        new_t = [t for t in sorted(ecdict_derived[lemma]) if t not in ecdict_words]
        if new_t:
            print(f"  {lemma} -> {', '.join(new_t[:6])}")
            count += 1

    if ecdict_derived:
        avg = total / len(ecdict_derived)
        print(f"\nAvg derived forms per 14k word: {avg:.1f}")


if __name__ == "__main__":
    main()
