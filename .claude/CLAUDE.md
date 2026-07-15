# 腕上词典 — Claude Code Rules

> **⚠️ MANDATORY: Before any Vela work (.ux, manifest, build, deploy, API), use the vela-dev skill**

## What this is

**腕上词典** (Wrist Dictionary) — a Xiaomi Vela QuickApp for Mi Band smartwatches. Built with aiot-toolkit. Single-page SFC format (.ux files: <template> + <script> + <style> in one file).

## Key config

| File | What |
|------|------|
| opencode.json | OpenCode configuration |
| .prettierrc.js | No semicolons, double quotes, no trailing commas, bracketSpacing: false, printWidth 100, 2-space indent |
| .stylelintrc.js | Allows custom Vela CSS props + :blur pseudo-class |
| commitlint.config.js | Conventional commits: bug, feat, fix, docs, style, refactor, test, chore, revert, merge |
| .eslintignore | Ignores dist/, build/, sign/, node_modules/ |
| .gitignore | Also ignores dist/, build/, sign/, src/common/dict/ (generated), .husky/, .codegraph/, .omo/ |

## Commands

| Command | What |
|---------|------|
| npm run start | Dev server (aiot start --watch) |
| npm run build | Build RPK (aiot build) |
| npm run release | Release build (aiot release) |
| npm run lint | ESLint --fix on src/ (.ux,.js) |
| npm run deploy:watch | Build + ADB push to emulator-5554 |
| npm run deploy:watch:fast | ADB push only (skip build) |

## Project structure

```
src/
  app.ux / manifest.json          — Entry + config
  pages/                          — 7 pages
    index/                        — Home with 4 buttons
    search/                       — IME + cursor editing + autocomplete
    results/                      — English/Chinese results
    detail/                       — Word detail + favorite toggle
    records/                      — History / favorites list (type param)
    about/                        — Credits, license
    sponsor/                      — Donation QR code
  components/
    InputMethod/                  — English QWERTY keyboard
  common/
    dict/                         — Generated shards (gitignored, do NOT edit)
    english_suggestions.js        — Letter-indexed word list by exam tag
scripts/                          — generate_watch_dict.py, deploy_watch.ps1
```

## Screen & style

- Canvas: 212x520px, designWidth: "device-width", minPlatformVersion: 1000
- Background #020813 on all pages except about (#000000)
- Blue/white/black dark theme
- **All text min 18px** — do not go below unless user OKs truncation

## Storage

| Key | Type | Max | Purpose |
|-----|------|-----|---------|
| dic_history | JSON array | 20 | Search history |
| dic_favorites | JSON array | 20 | Favorites |

Both via @system.storage. Dedup/toggle by normalized word.

## Dictionary (~128k Chinese phrases, 15k English headwords)

Source: ECDICT + CC-CEDICT + BNC/COCA word-family lists.
Regenerate: python scripts/generate_watch_dict.py (never edit shards directly).

## ANTI-PATTERNS

- **Never edit dictionary shard files** under src/common/dict/. Regenerate via python scripts/generate_watch_dict.py.
- **No type suppression** — no as any, @ts-ignore, @ts-expect-error.
- **No semicolons** — Prettier enforces no-semicolon style.
- **No empty catch blocks** — always handle or re-throw.
- **Don't remove swipe-back gesture** when adding new pages.
- **Don't override designWidth** — must stay "device-width" for the 212x520 canvas.
