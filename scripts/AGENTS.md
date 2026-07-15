# scripts/ — Build & Deploy

Two scripts. **Dict generation is Python**; **deploy is PowerShell**.

## Files

| File | Lines | Role |
|------|-------|------|
| `generate_watch_dict.py` | ~552 | Build `src/common/dict/` shards from `data/` CSVs + CC-CEDICT |
| `deploy_watch.ps1` | ~70 | Build RPK + `adb push` + install + launch on emulator-5554 |

## generate_watch_dict.py

Phases (in `main()`):
1. Read `data/ecdict_tagged_14942_compact.csv` rows (word/phonetic/translation/tag/exchange)
2. Write 26 compact English indexes: `words/word_<a-z>.txt`; row = `word<TAB>entryId<TAB>tag`
3. Build inflection graph: `inflect/` and `inflect_reverse/` (exchange + BNC/COCA word families + suffix rules in `derived_candidates()`)
4. Build canonical full entries: `entries/entry_<nn>.txt`, shard = `entryId // 500`
5. Build `zh_index/` (single-char entries) and `cn_index/` (Chinese phrase → entry IDs; ECDICT reverse lookup + CC-CEDICT augmentation)
6. Encode every Chinese ID list as strictly increasing delta-base36 tokens
7. Emit `meta.json` with schema/count stats and `resultLimit: 20`

Output root: `src/common/dict/`. Cleans dir on every run (`shutil.rmtree(OUT)`).

### Key functions
- `key_for(value)` — 2-char shard key used only by `inflect/` and `inflect_reverse/`
- `zh_bucket_for(char)` — bucket = `ord(char) % 64` → 2-hex filename
- `entry_shard_for(entry_id)` — canonical entry shard = `entry_id // 500`
- `encode_delta_base36(entry_ids)` / `decode_delta_base36(value)` — strict Chinese index ID codec
- `load_cc_cedict(path)` — parses `data/cedict.txt.gz` into `zh_phrase → [meanings]` dict
- `derived_candidates(word)` — suffix-stripping rules (-ily/-ly/-iness/-ness/-ment/-able/-ible/-ful/-less/-hood/-ship/-er/-or) for rule-based inflection

`entries/entry_<nn>.txt` is the only full word/phonetic/translation/tag store used to hydrate both English and Chinese results. Autocomplete asynchronously reuses the compact `word_<a-z>.txt` files. Do not add `index_en.txt` or `english_suggestions.js/.json` back.

### Run
```bash
python scripts/generate_watch_dict.py
```

## deploy_watch.ps1

```powershell
.\scripts\deploy_watch.ps1          # Build + push to emulator-5554
.\scripts\deploy_watch.ps1 -Serial 192.168.x.x:5555  # Target real device
.\scripts\deploy_watch.ps1 -NoBuild # Skip build, push existing RPK
```

### Flow
1. `npm run build` (or skip with `-NoBuild`)
2. Find newest `*.rpk` in `dist/`
3. `adb push` to device
4. `adb shell pm install <rpk_path>`
5. `adb shell am start` → verify with `am dump` checks for `[resumed]`

### Error handling
`$ErrorActionPreference = "Stop"` — exits on any failure.

## ANTI-PATTERNS

- **Don't edit dictionary shards** — run `generate_watch_dict.py` instead.
- **Don't use `-NoBuild` with stale RPKs** — ensures device has latest code.
