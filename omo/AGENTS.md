# omo/ — Helper Scripts (32 .py)

Asset generation, visual QC, dict coverage tests. **Not loaded by the app** — used by the build/release pipeline and for offline validation.

## Layout (themes)

```
omo/
├── gen_cover.py → gen_cover_v5s.py  # Cover image variants (1800×1200, 1200×800, 16:9)
├── gen_poster.py            # Poster generation (poster-qc.md workflow)
├── analyze_cccedict.py      # CC-CEDICT coverage/quality analysis
├── check_dates.py           # Validate date strings in build artifacts
├── check_pr.py              # PR sanity-check helper
├── coverage_test_v2.py      # 2nd-gen dict coverage (zh/en/exact/prefix)
├── dict_coverage_test.py    # Main coverage test — run via `python omo/dict_coverage_test.py`
├── dict_compaction_test.py  # Delta-base36 codec contract tests
├── dict_semantic_validator.py # Canonical counts/IDs/schema validation
├── measure_text.py          # Text measurement utility
├── qc_check.py              # Quality check helper
├── verify_pr.py             # PR verification
├── verify_rle.py            # RLE codec verification
├── _gen_*.py                # Asset generation (icons, buttons, icon-deco)
├── _process_icon*.py        # Icon processing pipeline
├── _check_*.py              # Validation utilities (sizes, WM)
├── _miss_analysis.json      # Coverage gap data
├── _pos_samples.txt         # Part-of-speech samples
├── last_qc_result.txt       # Latest visual QC feedback
├── yuanbao_python_*.py      # One-shot LLM-generated script (safe to remove)
└── wordnet_derived_test.py  # WordNet-derived inflection test
```

## Common patterns

- **Paths**: hardcoded to absolute Windows paths — `BASE = r'J:\code\MI band\腕上词典\release_repo'`
- **Fonts**: `msyhbd.ttc` / `msyh.ttc` / `msyhl.ttc` / `segoeui*.ttf` (system fonts)
- **Output**: always under `release_repo/` (cover.png, preview/*.png)
- **Skins**: read from `C:\Users\Administrator\.vela\sdk\skins\builtin\xiaomi_band_10\background_l.png`
- **PIL/ImageDraw** for poster generation; **requests** + zhipuai/GLM-4V-Flash for cloud visual-QC feedback (poster-qc.md workflow)

## Coverage test

`python omo/dict_coverage_test.py` reads the 26 `words/word_<a-z>.txt` compact indexes plus `cn_index/` and `zh_index/`, then validates:
- English exact/prefix match
- Chinese exact/prefix match
- Coverage percentage report

Compact-v3 rows use one-character Base36 front-coded words plus `entryId<TAB>tag`; full English and Chinese results hydrate from canonical front-coded `entries/entry_<nn>.txt`. Chinese index ID lists are strictly increasing Base64-ULEB128 values, with 96 cn buckets and 64 zh buckets. `dict_semantic_validator.py --require-compact` checks these contracts and rejects legacy `index_en.txt` / `dict_*.txt` layouts.

## ANTI-PATTERNS

- **Don't commit generated outputs** (cover.png, preview screenshots) from this directory — they live in `release_repo/`.
- **Don't leave stale one-shot scripts** (`yuanbao_python_*`).
- **Paths are Windows-absolute** — will fail on non-Windows. Refactor to relative if cross-platform needed.
