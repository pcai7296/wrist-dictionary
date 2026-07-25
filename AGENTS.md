# 腕上词典 — AGENTS.md

> **⚠️ MANDATORY: Before any Vela work (.ux, manifest, build, deploy, API), call skill(name="vela-dev") first — see .opencode/instructions/vela.md**

## What this is

**腕上词典** (Wrist Dictionary) — a Xiaomi Vela QuickApp for Mi Band smartwatches. Built with iot-toolkit (iot CLI). Single-page SFC format (.ux files: <template> + <script> + <style> in one file, parsed by prettier as Vue).

## Key config

| File | What |
|------|------|
| opencode.json | Loads AGENTS.md + .opencode/instructions/vela.md + poster-qc.md |
| .opencode/instructions/conventions.md | Font-size rules (min 18px), about page multi-screen layout, emulator policy |
| .opencode/instructions/dictionary-coverage.md | Dict coverage analysis + CC-CEDICT integration |
| .opencode/instructions/poster-qc.md | Poster generation + GLM-4V-Flash visual QA workflow |
| .prettierrc.js | No semicolons, double quotes, no trailing commas, racketSpacing: false, printWidth 100, 2-space indent. .ux parsed as Vue |
| .stylelintrc.js | Allows custom Vela CSS props + :blur pseudo-class |
| commitlint.config.js | Conventional commits: ug, eat, ix, docs, style, efactor, 	est, chore, evert, merge |
| .eslintignore | Ignores dist/, uild/, sign/, 
ode_modules/ |
| .gitignore | Also ignores dist/, uild/, sign/, src/common/dict/ (generated), .husky/, .codegraph/, .omo/ |

No .eslintrc* — ESLint defaults via iot-toolkit.

## Commands

| Command | What |
|---------|------|
| 
pm run start | Dev server (iot start --watch) |
| 
pm run build | Build RPK (iot build) |
| 
pm run release | Release build (iot release) |
| 
pm run lint | ESLint --fix on src/ (.ux,.js) |
| 
pm run deploy:watch | Build + ADB push to emulator-5554 |
| 
pm run deploy:watch:fast | ADB push only (skip build) |

uild/ and dist/ are gitignored — outputs of spack v1.7.12 via iot-toolkit.

## Deploy

- scripts/deploy_watch.ps1 — PowerShell. Targets emulator-5554. Override: -Serial 192.168.x.x:5555 or -NoBuild.
- Flow: build → newest *.rpk in dist/ → db push → db shell pm install → db shell am start → verify m dump checks [resumed].
- $ErrorActionPreference = "Stop" — exits on any failure.

## Real device management

ork_astrobox/ — AstroBox CLI fork for multi-device management (pairing, RPK install via queue).

## Pre-commit

Run ash husky.sh once (requires git):
- Pre-commit via lint-staged: Prettier → ESLint (.ux/.js); Prettier → stylelint (./less/.css)
- Commit-msg via commitlint

## Project structure

`
src/
  app.ux / manifest.json          — Entry + config
  pages/                          — 8 pages
    index/                        — Home with 4 buttons
    search/                       — IME + cursor editing + autocomplete
    results/                      — English/Chinese results (1425 lines)
    filter/                       — Letter drill-down jump-search
    detail/                       — Word detail + favorite toggle (661 lines)
    records/                      — History / favorites list (type param)
    about/                        — Credits, license, multi-screen adaptive usage text
    sponsor/                      — Donation QR code
  components/
    InputMethod/                  — English QWERTY keyboard (890 lines), sub-assets for layouts
  common/
    dict/                         — Generated shards (gitignored, do NOT edit)
    icons/                        — Button/decoration icons
  i18n/                           — Locale JSON files (defaults, en, zh-CN)
scripts/                          — generate_watch_dict.py, deploy_watch.ps1
omo/                              — 32 Python scripts for asset gen, poster, coverage tests
data/                             — Source dict CSVs (ecdict_tagged_14942_compact.csv, cedict.txt.gz)
release_repo/                     — Published RPK + cover.png + preview screenshots
`

## Screen & style

- Canvas: 212x520px, designWidth: "device-width", minPlatformVersion: 1000
- Background #020813 on all pages except about (#000000)
- Blue/white/black dark theme
- **All text min 18px** — do not go below unless user OKs truncation
- **About page**: usage text wraps by screen profile; 466×466 uses the same safe width as results.

## Storage

| Key | Type | Max | Purpose |
|-----|------|-----|---------|
| dic_history | JSON array | 20 | Search history |
| dic_favorites | JSON array | 20 | Favorites |

Both via @system.storage. Dedup/toggle by normalized word.

## Router

Features: system.router, system.vibrator, system.device, system.file, system.storage, system.prompt (toast).

7 pages in manifest.json, entry = pages/index.

## Dictionary (~128k Chinese phrases, 15k English headwords)

Source: ECDICT + CC-CEDICT + BNC/COCA word-family lists.
Regenerate: python scripts/generate_watch_dict.py (never edit shards directly).

| Feature | Mechanism |
|---------|-----------|
| English lookup | 26 first-letter files (`words/word_a.txt`..`word_z.txt`); row = `word<TAB>entryId<TAB>tag` |
| Chinese lookup | Unicode codepoint % 64 to 64 bucket files; ID lists are strictly decoded delta-base36 |
| Inflect lookup | `inflect/` + `inflect_reverse/`; `key_for()` 2-char sharding is used only here |
| Entry lookup | `entries/entry_<nn>.txt`, sharded by `entryId / 500`; canonical full data for English and Chinese hydration |
| Fuzzy search | Edit distance <=2, scan <=4000 words, pool <=80 candidates |
| Autocomplete | Async read/cache of the same compact `word_<a-z>.txt` index; exam tag affects ranking |
| Results cap | 20 |

There is no `index_en.txt` or `english_suggestions.js/.json` runtime resource.

Coverage: English 100%, Chinese ~86% (14 modern words missing from CC-CEDICT).
Test: python omo/dict_coverage_test.py

## InputMethod component

- English QWERTY only
- Emits: isibilityChange, keyDown, delete, complete
- Asset paths use {{lang}} variable — handled by iot-toolkit 2.0.4+

## Swipe-back gesture (every page)

| Page | Start X <= | End X >= | dY <= |
|------|------------|----------|-------|
| Most pages | 53 | 159 | 120 |
| about.ux | 20 | 180 | 60 |

Copy pattern from any page except about. Needs getTouchPoint() + 	ouchStartX/Y.

## Router quirks

- **records to search**: outer.replace (not push) with utoSearch="1"
- **detail to results** (inflect): outer.replace (not push)
- **Detail page**: 1s cooldown on inflect button, max 3 depth levels

## VSCode MCP

elajs-mcp in .vscode/mcp.json with auto-approved: tap, screenshot, navigate, input text, build, get device logs, storage inspect.

## Emulator policy

**Do not touch the emulator unless asked.** Verification is the user's job (per conventions.md).

## Tests & CI

- **Offline tests**: `omo/dict_coverage_test.py`, `omo/dict_compaction_test.py`, `omo/dict_semantic_validator.py`
- **Test framework / CI**: No app test framework. No GitHub Actions.

## ANTI-PATTERNS (THIS PROJECT)

- **Never edit dictionary shard files** under src/common/dict/. Regenerate via python scripts/generate_watch_dict.py.
- **No static asset paths** with {{lang}} — iot-toolkit 2.0.4+ handles variable-depth paths.
- **No type suppression** — no s any, @ts-ignore, @ts-expect-error.
- **No semicolons** — Prettier enforces no-semicolon style.
- **No empty catch blocks** — always handle or re-throw.
- **Don't remove swipe-back gesture** when adding new pages.
- **No generic AI boilerplate** — match project's telegraphic, no-fluff style.
- **Don't override designWidth** — must stay "device-width" for the 212x520 canvas.
- **ESLint runs with --fix by default** — it auto-formats on lint. Be aware before running 
pm run lint.

## CODE MAP

| Symbol | Type | File | Role |
|--------|------|------|------|
| key_for() | function | scripts/generate_watch_dict.py | Generate 2-char shard key for inflect / reverse-inflect files only |
| zh_bucket_for() | function | scripts/generate_watch_dict.py | Unicode bucket for Chinese index |
| load_cc_cedict() | function | scripts/generate_watch_dict.py | Parse CC-CEDICT into cn_index |
| SimpleInputMethod | object | src/components/InputMethod/assets/dicUtil.js | English dict query orchestration |
| decodeDeltaIds() | function | src/pages/results/results.ux | Strictly decode delta-base36 Chinese index IDs |
| loadEnglishSuggestionSource() | function | src/pages/search/search.ux | Async load/cache compact first-letter word index |
