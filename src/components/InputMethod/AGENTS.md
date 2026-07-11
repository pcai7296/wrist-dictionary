# InputMethod — IME Component

**InputMethod.ux** — English QWERTY keyboard IME for watch dictionary input.

## Structure

```
InputMethod/
├── InputMethod.ux        # Main component: keyboard layout + logic + styles
└── assets/
    └── full/             # QWERTY full keyboard key images
```

## Events emitted

| Event | Payload | Description |
|-------|---------|-------------|
| `visibilityChange` | `{ visible: bool }` | IME shown/hidden |
| `keyDown` | `{ key: string }` | Character input |
| `delete` | — | Backspace |
| `complete` | — | Input confirmed / commit |

## Key flow

1. User taps key → `keyDown` event → parent handles input buffer
2. Parent updates buffer → IME recomputes autocomplete candidates
3. User confirms → `complete` event → parent submits

## CONVENTIONS

- All key images are PNG assets stored in `assets/full/`
- Variable-depth paths use `{{lang}}` — `aiot-toolkit 2.0.4+` resolves these

## ANTI-PATTERNS

- Don't hardcode asset paths — use the `{{lang}}` variable-depth pattern
- Don't add new key image formats (keep PNG)
