# 腕上词典 — AGENTS.md

> **⚠️ MANDATORY: Before any Vela work (.ux, manifest, build, deploy, API), call `skill(name="vela-dev")` first — see `.opencode/instructions/vela.md`**

## What this is

**腕上词典** (Wrist Dictionary) — a Xiaomi Vela Quick App (快应用) for Mi Band smartwatches. Built with `aiot-toolkit` (`aiot` CLI). Single-page SFC format (`.ux` files: `<template>` + `<script>` + `<style>` in one file, parsed by prettier as Vue).

## Quick commands

| Command | What it does |
|---|---|
| `npm run start` | Dev server (`aiot start --watch`) |
| `npm run build` | Build RPK (`aiot build`) |
| `npm run release` | Release build (`aiot release`) |
| `npm run lint` | ESLint on `src/` (`--ext .ux,.js`) |
| `npm run deploy:watch` | Build + ADB push to watch |
| `npm run deploy:watch:fast` | ADB push only (skip build) |

## Code style (Prettier enforced)

- No semicolons, double quotes, no trailing commas, `bracketSpacing: false`
- Print width 100, 2-space indent
- `.ux` files parsed as Vue
- `lint-staged` runs Prettier → ESLint/stylelint → `git add` on commit

## Commit convention

Commitlint enforces conventional commits with custom types: `bug`, `feat`, `fix`, `docs`, `style`, `refactor`, `test`, `chore`, `revert`, `merge`.

## Project structure

```
src/
  app.ux                       — App lifecycle (onCreate/onDestroy)
  manifest.json                — Router, features, package config
  pages/
    index/                     — Home (entry page)
    search/                    — Search with IME, cursor editing
    results/                   — Search results (English + Chinese lookup)
    detail/                    — Word detail with favorite toggle
    records/                   — History or favorites list (type param)
    about/                     — Credits, license
    sponsor/                   — Donation QR code
  components/
    InputMethod/               — Full IME (QWERTY/T9, cn/en/jp, 3 screen shapes)
  common/
    dict/                      — Generated dictionary shards (do NOT edit manually)
    logo.png                   — App icon
  i18n/                        — Placeholder i18n (en.json, zh-CN.json, defaults.json)
scripts/
  deploy_watch.ps1             — ADB deploy: push RPK → install → start → verify
  generate_watch_dict.py       — Dictionary generator from ECDICT CSV
data/                          — Source dictionary CSV files
design/                        — Home screen spec and SVG
sign/                          — Signing keys
build/                         — Build output (rspack-bundled)
dist/                          — .rpk packages (gitignored)
```

## Key architecture facts

- **7 pages**, entry is `pages/index`. Router defined in `src/manifest.json`.
- **Router features**: `system.router`, `system.vibrator`, `system.device`, `system.file`, `system.storage`.
- **Storage keys**: `dic_history` (search history, max 20), `dic_favorites` (max 20). Both plain JSON arrays in `@system.storage`.
- **Screen**: Canvas is 212×520px. Background `#020813`. Blue/white/black color scheme.
- **Dictionary**: 14,942 headwords from [ECDICT](https://github.com/skywind3000/ECDICT) (MIT), plus BNC/COCA word-family data from EAP Foundation. File-based lookup via sharded text files in `src/common/dict/`. Results capped at 20.

## Dictionary internals

- **English lookup**: Words sharded by 2-char prefix key (`keyFor()`). `index_en.txt` maps first letter → shard names for single-character queries.
- **Chinese lookup**: Chinese-only chars in translation are indexed by Unicode `codepoint % 64` into 64 bucket files (`zh_00.txt`..`zh_3f.txt`). Each maps a Chinese char → list of entry IDs.
- **Inflect lookup**: Inflected forms map back to headwords via `inflect/` shards.
- **Entry lookup**: Entries sharded by `entryId / 500`. Used only for Chinese search path.
- **Generated code**: Run `python scripts/generate_watch_dict.py` to regenerate. Sources are `data/ecdict_tagged_14942_compact.csv` and optional `data/bnc_coca_word_family_lists_v2.xlsx`. Never edit shard files directly.

## InputMethod component

- Supports 3 screen shapes: `circle` (480×321 keyboard area), `rect` (rectangular), `pill-shaped` (capsule/跑道屏).
- Keyboard modes: `QWERTY` (full) and `T9`.
- Languages: Chinese (pinyin), English, Japanese (romaji→kana).
- IME data lives in `src/components/InputMethod/assets/`: `dic.js` (pinyin→hanzi), `dic_jp.js` (romaji→kanji), `dicUtil.js` (orchestrator).
- Emits events: `visibilityChange`, `keyDown`, `delete`, `complete`.
- Variable-depth asset paths use `{{lang}}` etc. — this was fixed in `aiot-toolkit 2.0.4` (don't try to use static paths).

## ADB deploy quirks

- `deploy_watch.ps1` targets `emulator-5554` by default. Override: `-Serial 192.168.x.x:5555`.
- Flow: build → find newest `.rpk` in `dist/` → `adb push` to `/data/app/com.watch.dic.rpk` → `adb shell pm install` → `adb shell am start` → verify via `am dump`.
- The deploy script uses strict `$ErrorActionPreference = "Stop"` and exits on any failure.

## Swipe-back gesture (every page)

Copy-pasted pattern across all 7 pages:
```js
// Touch starts in left quarter (x ≤ 53), ends at right quarter (x ≥ 159),
// mostly horizontal (Δy ≤ 120) → router.back()
```
If adding a new page, copy this gesture handler.

## VSCode MCP

`velajs-mcp` is configured in `.vscode/mcp.json` for debugging: tap, screenshot, input text, build, get device logs, navigate, etc.

## Stylelint quirks

Custom Vela CSS properties that stylelint would flag — ignored via config:
`placeholder-color`, `gradient-start`, `gradient-center`, `gradient-end`, `caret-color`, `selected-color`, `block-color`.

Selector pseudo-class `:blur` is also ignored (not standard CSS).

## Build output

- Build uses `rspack` (v1.7.12) under the hood via `aiot-toolkit`.
- Output directory: `build/` (intermediate), `dist/` (final .rpk).
- `build/` files are committed; `dist/` is gitignored.
- `node` >= 8.10 required (very old floor — actual dev likely uses Node 20+).

## CONVENTIONS (THIS PROJECT)

| Rule | Detail |
|------|--------|
| **String quotes** | Double quotes only |
| **Semicolons** | None |
| **Trailing commas** | None |
| **Indent** | 2 spaces |
| **Print width** | 100 |
| **Swipe-back gesture** | Every page: touch start x≤53, end x≥159, Δy≤120 → `router.back()` |
| **Storage keys** | `dic_history` (max 20), `dic_favorites` (max 20) — plain JSON arrays |
| **Result cap** | Dictionary search results never exceed 20 |
| **Dictionary data** | Generated — never edit `src/common/dict/` shards manually |
| **Screen** | Canvas 212×520px, background `#020813`, blue/white/black scheme |
| **Router features** | `system.router`, `system.vibrator`, `system.device`, `system.file`, `system.storage` |

## ANTI-PATTERNS (THIS PROJECT)

- **Never edit dictionary shard files** under `src/common/dict/`. Run `python scripts/generate_watch_dict.py` to regenerate from CSV source.
- **No static asset paths** with `{{lang}}` variables — `aiot-toolkit 2.0.4+` handles variable-depth paths; don't hardcode.
- **No type suppression** — never use `as any`, `@ts-ignore`, `@ts-expect-error`.
- **No semicolons** — Prettier enforces no-semicolon style.
- **No empty catch blocks** — always handle or re-throw.
- **Don't remove swipe-back gesture** when adding new pages — copy the pattern from existing pages.
- **No generic AI boilerplate** — match project's telegraphic, no-fluff style.

## CODE MAP (from codegraph)

| Symbol | Type | File | Role |
|--------|------|------|------|
| `key_for()` | function | `scripts/generate_watch_dict.py:24` | Generate 2-char shard key for word |
| `zh_bucket_for()` | function | `scripts/generate_watch_dict.py:43` | Unicode bucket for Chinese index |
| `SimpleInputMethod` | object | `src/components/InputMethod/assets/dicUtil.js` | Pinyin→Hanzi + Romaji→Kana orchestration |

## UNIQUE STYLES

- **`.ux` files** parsed as Vue by Prettier (single-file components with `<template>` + `<script>` + `<style>`)
- **Vela CSS properties** ignored by stylelint: `placeholder-color`, `gradient-start`, `gradient-center`, `gradient-end`, `caret-color`, `selected-color`, `block-color`
- **`:blur` pseudo-class** also ignored by stylelint (not standard CSS)
- **Commit types**: `bug`, `feat`, `fix`, `docs`, `style`, `refactor`, `test`, `chore`, `revert`, `merge`
