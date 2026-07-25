# Pages — Vela QuickApp Page Modules

## Overview

8 page modules for the wrist dictionary app. Each page is a self-contained .ux SFC.

## Structure

```
pages/
├── index/       # Home — 4 main buttons + about/sponsor links (318 lines)
├── search/      # IME input + cursor editing + autocomplete (728 lines)
├── results/     # English/Chinese search results (1425 lines)
├── filter/      # Letter/navigation drill-down to jump-search words (290 lines)
├── detail/      # Word detail + favorite toggle (661 lines, 1s cooldown)
├── records/     # History/favorites list (type param, 462 lines)
├── about/       # Credits, license — #000000 bg, text clipping known issue (367 lines)
└── sponsor/     # Donation QR code (120 lines)
```

## Where to Look

| Task | Location | Notes |
|------|----------|-------|
| Add new page | Create dir + .ux + register in manifest.json | Copy swipe-back gesture from existing page |
| Modify search flow | search/ + results/ | IME events → search logic → display |
| Letter drill-down | filter/ | Alphabetical jump-search with input mode |
| Edit word display | detail/ | Favorite toggle uses @system.storage |
| Change home layout | index/ | 4 main buttons + 2 secondary |
| List management | records/ | Accepts `type` param (history/favorites) |

## Swipe-back gesture (every page)

| Page | Start X <= | End X >= | dY <= |
|------|------------|----------|-------|
| Most pages | 53 | 159 | 120 |
| about.ux | 20 | 180 | 60 |

Copy pattern from any page except about. Uses `getTouchPoint()` + `touchStartX/Y`.

## Conventions

- **Background**: `#020813` on all pages except about (`#000000`)
- **Text size**: Minimum 18px. Do not go below unless user OKs truncation.
- **Router quirks**: records→search uses `router.replace` with `autoSearch="1"`; detail→results (inflect) uses `router.replace`.
