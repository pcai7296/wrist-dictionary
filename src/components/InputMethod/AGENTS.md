# InputMethod — IME Component

**InputMethod.ux** — Full input method engine (842 LOC). Supports 3 screen shapes, 2 keyboard modes, 3 input languages.

## Structure

```
InputMethod/
├── InputMethod.ux        # Main component: layout + logic + styles
└── assets/
    ├── dic.js            # Pinyin → Hanzi mapping data
    ├── dic_jp.js         # Romaji → Kana mapping data
    ├── dicUtil.js        # Dict query orchestrator (49 LOC)
    ├── full/             # QWERTY full keyboard key images
    ├── horizontal/       # Pill-shaped (跑道屏) key images
    ├── arc/              # Circular screen key images
    └── t9/               # T9 keypad key images
```

## Screen shapes

| Shape | Asset dir | KB area | Notes |
|-------|-----------|---------|-------|
| `circle` | `assets/arc/` | 480×321 | Circular watch face |
| `rect` | `assets/full/` | full | Rectangular screen |
| `pill-shaped` | `assets/horizontal/` | horizontal | Capsule/跑道屏 |

## Keyboard modes

- **QWERTY** — Full keyboard (`assets/full/`)
- **T9** — Phone keypad (`assets/t9/`)

## Input languages

- **`en`** — English (no candidate lookup, pass-through)
- **`cn`** — Chinese pinyin → Hanzi via `dic.js` + `dicUtil.js`
- **`jp`** — Japanese romaji → Kana via `dic_jp.js`

## Events emitted

| Event | Payload | Description |
|-------|---------|-------------|
| `visibilityChange` | `{ visible: bool }` | IME shown/hidden |
| `keyDown` | `{ key: string }` | Character input |
| `delete` | — | Backspace |
| `complete` | — | Input confirmed / commit |

## Key flow

1. User taps key → `keyDown` event → parent handles input buffer
2. Parent updates buffer → IME recomputes candidates via `dicUtil`
3. User selects candidate / confirms → `complete` event → parent commits
4. Language switch toggles between en/cn/jp dict lookups

## CONVENTIONS

- All key images are PNG assets stored per-screen-shape directory
- Variable-depth paths use `{{lang}}` — `aiot-toolkit 2.0.4+` resolves these
- `dicUtil.js` initializes dict on import (side effect at module level)
- T9 mode reuses letter mappings across screen shapes

## ANTI-PATTERNS

- Don't hardcode asset paths — use the `{{lang}}` variable-depth pattern
- Don't add new key image formats (keep PNG)
- Don't bypass `dicUtil.js` to access raw dict data
