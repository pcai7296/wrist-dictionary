# data/ — Source Dictionary Inputs

Inputs to `scripts/generate_watch_dict.py`. **Source-of-truth — not regenerated.**

## Files

| File | Size | Role |
|------|------|------|
| `ecdict_tagged_14942_compact.csv` | ~1.6 MB | Primary English headword corpus (14,942 rows). Required. |
| `ecdict_tagged_14942_compact.json` | ~2.5 MB | Same data in JSON for quick inspection. |
| `ecdict_tagged_14942_full.csv` | ~3.7 MB | Full ECDICT fields (used for analysis, not generation). |
| `ecdict_tagged_14942_stats.json` | ~0.9 KB | Tag statistics. |
| `cedict.txt.gz` | ~3.9 MB | CC-CEDICT Chinese→English dictionary. **Optional** — see below. |
| `bnc_coca_word_family_lists_v2.xlsx` | ~1.2 MB | BNC/COCA word family list (used to augment ECDICT inflection graph via `load_word_family_links()`). Optional. |

## CSV format (`ecdict_tagged_14942_compact.csv`)

Columns (consumed by `generate_watch_dict.py` via `csv.DictReader`):
- `word`, `phonetic`, `translation`, `tag` (exam tags), `exchange` (inflection codes: `s:`/`d:`/`p:`/`i:`/`3:`/`r:`/`t:`)

## CC-CEDICT integration

Header (used in `load_cc_cedict()`):
```python
CCEDICT_URL = "https://www.mdbg.net/chinese/export/cedict/cedict_1_0_ts_utf-8_mdbg.txt.gz"
CCEDICT_SOURCE = ROOT / "data" / "cedict.txt.gz"
```

If absent, the script prints:
```
  [CC-CEDICT] 文件不存在: <path>
  [CC-CEDICT] 请下载: <url>
```
…and continues without reverse-Chinese enrichment (Chinese coverage drops from ~100% to ~86%).

## ANTI-PATTERNS

- **Don't hand-edit** these files — they come from upstream projects (ECDICT, MDBG, EAP BNC/COCA). Edit the upstream or patch in `generate_watch_dict.py`.
