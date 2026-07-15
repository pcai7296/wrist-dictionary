# InputMethod — IME Component

**InputMethod.ux** — Multi-layout keyboard IME for watch dictionary. Supports 3 screen shapes × 4 keyboard layouts, with Chinese/English/Japanese input.

## Structure

```
InputMethod/
├── InputMethod.ux        # ~800 lines: template + script + styles
├── AGENTS.md
└── assets/
    ├── full/             # QWERTY full keys for circle (62-round) screen
    ├── arc/              # Keys for pill-shaped (66-capsule) screen
    ├── horizontal/       # Keys for rect (67-square) screen
    ├── t9/               # T9 keypad keys
    ├── dic.js            # 6763 Chinese characters (pinyin→hanzi map)
    ├── dicUtil.js        # SimpleInputMethod query orchestration
    └── dic_jp.js         # Japanese romaji→kanji mapping
```

## Props

| Prop | Default | Description |
|------|---------|-------------|
| `hide` | `true` | Show/hide IME |
| `keyboardtype` | `"QWERTY"` | `"QWERTY"` or `"T9"` |
| `maxlength` | `5` | Max visible suggestion slots |
| `vibratemode` | `""` | Vibration on keystroke (empty = off) |
| `screentype` | `"circle"` | `"circle"` (62-round), `"rect"` (67-square), or `"pill-shaped"` (66-capsule) |

## Events

| Event | Payload | Description |
|-------|---------|-------------|
| `visibilityChange` | `{ visible: bool }` | IME shown/hidden |
| `keyDown` | `{ key: string }` | Character input |
| `delete` | — | Backspace |
| `complete` | `{ content: string }` | Input confirmed / commit |
| `ready` | — | IME component mounted |

## Key flow

1. User taps key → `keyDown` event → parent handles input buffer
2. Parent updates buffer → IME recomputes autocomplete candidates
3. User confirms → `complete` event → parent submits

## CONVENTIONS

- All key images are PNG assets stored per layout (`full/`, `arc/`, `horizontal/`, `t9/`)
- Asset paths use `{{lang}}` variable — handled by `aiot-toolkit 2.0.4+`

## ANTI-PATTERNS

- Don't hardcode asset paths — use the `{{lang}}` variable-depth pattern
- Don't add new key image formats (keep PNG)
