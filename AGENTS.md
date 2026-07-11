# 腕上词典 — AGENTS.md

> **⚠️ MANDATORY: Before any Vela work (.ux, manifest, build, deploy, API), call `skill(name="vela-dev")` first — see `.opencode/instructions/vela.md`**

## What this is

**腕上词典** (Wrist Dictionary) — a Xiaomi Vela QuickApp for Mi Band smartwatches. Built with `aiot-toolkit` (`aiot` CLI). Single-page SFC format (`.ux` files: `<template>` + `<script>` + `<style>` in one file, parsed by prettier as Vue).

## Key config

| File | What |
|------|------|
| `opencode.json` | Instructs OpenCode to load `AGENTS.md` + `.opencode/instructions/vela.md` |
| `.opencode/instructions/conventions.md` | Font-size rules (min 18px), known issues (about page text clipping), emulator policy |
| `.opencode/instructions/dictionary-coverage.md` | Dictionary coverage analysis + CC-CEDICT integration details |
| `.prettierrc.js` | No semicolons, double quotes, no trailing commas, `bracketSpacing: false`, printWidth 100, 2-space indent. `.ux` parsed as Vue. |
| `.stylelintrc.js` | Allows custom Vela CSS properties (`placeholder-color`, `gradient-*`, `caret-color`, etc) and `:blur` pseudo-class |
| `commitlint.config.js` | Conventional commits with custom types: `bug`, `feat`, `fix`, `docs`, `style`, `refactor`, `test`, `chore`, `revert`, `merge` |
| `.eslintignore` | Ignores `dist/`, `build/`, `sign/`, `node_modules/` |
| `.gitignore` | Also ignores `dist/`, `build/`, `sign/`, `src/common/dict/` (generated), `.husky/`, `.codegraph/`, `.omo/` |

No `.eslintrc*` file exists in the repo — ESLint defaults are applied via `aiot-toolkit`.

## Commands

| Command | What it does |
|---|---|
| `npm run start` | Dev server (`aiot start --watch`) |
| `npm run build` | Build RPK (`aiot build`) |
| `npm run release` | Release build (`aiot release`) |
| `npm run lint` | ESLint with `--fix` on `src/` (`--ext .ux,.js`) |
| `npm run deploy:watch` | Build + ADB push to emulator-5554 |
| `npm run deploy:watch:fast` | ADB push only (skip build) |

`build/` and `dist/` are both gitignored — outputs of `rspack` v1.7.12 via `aiot-toolkit`.

## Deploy

- `scripts/deploy_watch.ps1` — PowerShell. Targets `emulator-5554` by default. Override: `npm run deploy:watch -- -Serial 192.168.x.x:5555` or `-NoBuild` for RPK-only push.
- Flow: build → find newest `*.rpk` in `dist/` → `adb push` → `adb shell pm install` → `adb shell am start` → verify via `am dump` (checks `[resumed]` state).
- Always runs with `$ErrorActionPreference = "Stop"` — exits on any failure.

## Real device management

`fork_astrobox/` — a fork of AstroBox CLI for managing multiple real watches (pairing, RPK install via queue). Only needed if deploying to real hardware beyond a single device.

## Pre-commit setup

Run `bash husky.sh` once (requires git) to install hooks:
- Pre-commit via `lint-staged`: Prettier → ESLint (`.ux/.js`); Prettier → stylelint (`./less/.css`)
- Commit-msg via commitlint

## Project structure

```
src/
  app.ux                                — App lifecycle (onCreate/onDestroy)
  manifest.json                         — Router, features, package config
  pages/
    index/                               — Home with 4 main buttons
    search/                              — IME + cursor editing + autocomplete
    results/                             — English/Chinese lookup results
    detail/                              — Word detail with favorite toggle
    records/                             — History or favorites list (type param)
    about/                               — Credits, license, tag reference
    sponsor/                             — Donation QR code
  components/
    InputMethod/                         — English keyboard IME (QWERTY, cursor control, autocomplete)
  common/
    dict/                                — Generated dictionary shards (gitignored, do NOT edit)
    english_suggestions.js               — Letter-indexed word list with exam tags
    icons/                               — Button and decoration icons
scripts/
  deploy_watch.ps1                       — ADB deploy
  generate_watch_dict.py                 — Dictionary generator (ECDICT + CC-CEDICT + BNC/COCA)
data/                                    — Source dictionary CSV files (ecdict_tagged_14942_compact.csv, cedict.txt.gz)
omo/                                     — Auxiliary Python scripts (icon gen, coverage tests, analysis)
  dict_coverage_test.py                  — Offline dictionary hit-rate test
  coverage_test_v2.py                    — V2 coverage test
  _gen_*.py                              — Icon/asset generation scripts
sign/                                    — Signing keys (gitignored)
collect-ux-review.ps1                    — Gathers all .ux files into one review bundle
```

## 7 pages, router in manifest.json

Router features declared in manifest: `system.router`, `system.vibrator`, `system.device`, `system.file`, `system.storage`, **`system.prompt`** (toast messages on search/results/detail).

## Screen & style

- Canvas: 212×520px, `designWidth: "device-width"`, `minPlatformVersion: 1000`
- Background `#020813` on all pages except about (`#000000`)
- Blue/white/black color scheme, dark theme
- **All text min 18px** — do not go below unless user explicitly OKs truncation (per `conventions.md`)

## Storage

- `dic_history` — search history, plain JSON array, max 20 items
- `dic_favorites` — favorites, plain JSON array, max 20 items
- Both via `@system.storage`. Dedup/toggle by normalized word.

## Dictionary (~128k Chinese phrases, 15k English headwords)

Source data: ECDICT + CC-CEDICT + BNC/COCA word-family lists. File-based lookup via sharded text files in `src/common/dict/`. Regenerate with:

```bash
python scripts/generate_watch_dict.py
# optional: place data/bnc_coca_word_family_lists_v2.xlsx for word-family data
```

Never edit shard files directly.

### Lookup architecture

| What | How |
|------|-----|
| English lookup | Words sharded by 2-char prefix key (`key_for()`). `index_en.txt` maps first-letter → shard names. |
| Chinese lookup | Chinese-only chars indexed by Unicode `codepoint % 64` → 64 bucket files (`zh_00.txt`..`zh_3f.txt`). Each maps char → entry IDs. CC-CEDICT phrases merged into same buckets. |
| Inflect lookup | Inflected forms → headwords via `inflect/` shards + `inflect_reverse/` reverse index. |
| Entry lookup | Entries sharded by `entryId / 500`. Used for Chinese search path only. |
| Fuzzy search | Edit distance (max 2) over shard text, scanned up to 4000 words, pool capped at 80 candidates. |
| Autocomplete | `ENGLISH_SUGGESTION_BUCKETS` in `english_suggestions.js` — letter-indexed with exam tags (zk/gk/cet4/cet6/ky/toefl/ielts/gre). |
| Results capped at 20. | |

### Coverage

- English exact/prefix match: 100%
- Chinese exact match: ~86% (14 modern synthetic words not in CC-CEDICT — see `.opencode/instructions/dictionary-coverage.md`)
- Test: `python omo/dict_coverage_test.py`

## InputMethod component

- English QWERTY keyboard only
- Emits: `visibilityChange`, `keyDown`, `delete`, `complete`
- Variable-depth asset paths use `{{lang}}` — `aiot-toolkit 2.0.4+` handles this; don't use static paths.

## Swipe-back gesture (every page)

| Page | Start X ≤ | End X ≥ | ΔY ≤ |
|------|-----------|---------|------|
| Most pages | 53 | 159 | 120 |
| about.ux | 20 | 180 | 60 |

If adding a page, copy the pattern from any page except about. Needs `getTouchPoint()` and `touchStartX/Y` state vars.

## Router navigation quirks

- **records → search** (history item click): uses `router.replace` (not push) with `queryParam` + `autoSearch="1"`.
- **detail → results** (inflect button): uses `router.replace` (not push) to avoid stacking.
- **Detail page**: 1s cooldown on inflect button, max 3 levels of depth.

## VSCode MCP

`velajs-mcp` in `.vscode/mcp.json` with auto-approved: tap, screenshot, navigate, input text, build, get device logs, storage inspect, etc.

## Emulator policy

**Do not touch the emulator unless the user explicitly asks.** Verification is the user's job (per `conventions.md`).

## Tests & CI

- **Tests**: None. No test framework.
- **CI**: None. No GitHub Actions.

## ANTI-PATTERNS (THIS PROJECT)

- **Never edit dictionary shard files** under `src/common/dict/`. Regenerate via `python scripts/generate_watch_dict.py`.
- **No static asset paths** with `{{lang}}` — `aiot-toolkit 2.0.4+` handles variable-depth paths.
- **No type suppression** — no `as any`, `@ts-ignore`, `@ts-expect-error`.
- **No semicolons** — Prettier enforces no-semicolon style.
- **No empty catch blocks** — always handle or re-throw.
- **Don't remove swipe-back gesture** when adding new pages.
- **No generic AI boilerplate** — match project's telegraphic, no-fluff style.
- **Don't override `designWidth`** — must stay `"device-width"` for the 212×520 canvas.
- **ESLint runs with `--fix` by default** — it auto-formats on lint. Be aware before running `npm run lint`.

## CODE MAP

| Symbol | Type | File | Role |
|--------|------|------|------|
| `key_for()` | function | `scripts/generate_watch_dict.py:29` | Generate 2-char shard key for word |
| `zh_bucket_for()` | function | `scripts/generate_watch_dict.py:48` | Unicode bucket for Chinese index |
| `load_cc_cedict()` | function | `scripts/generate_watch_dict.py:67` | Parse CC-CEDICT into cn_index |
| `SimpleInputMethod` | object | `src/components/InputMethod/assets/dicUtil.js` | English dict query orchestration |
| `ENGLISH_SUGGESTION_BUCKETS` | object | `src/common/english_suggestions.js:1` | Letter-indexed word lists with exam tags |
