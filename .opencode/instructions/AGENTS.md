# .opencode/instructions/ — Agent Rules + References

Loaded by `opencode.json` (configuration: `instructions: ["AGENTS.md", ".opencode/instructions/vela.md", ".opencode/instructions/poster-qc.md"]`).

## Files

| File | Topic |
|------|-------|
| `vela.md` | **MANDATORY** — must be read before any Vela work (.ux, manifest, build, deploy, API). Points to `skill(name="vela-dev")`. |
| `poster-qc.md` | Standardized poster/cover-design iteration flow (GLM-4V-Flash visual QC loop). |
| `conventions.md` | Project-level rules: min 18px font, no emulator touching without ask, about-page multi-screen layout. |
| `dictionary-coverage.md` | Dict coverage analysis + CC-CEDICT integration notes. |

## Roles

- **Mandatory** (enforced via `opencode.json`): `vela.md`, `poster-qc.md`.
- **On-demand** (referenced from instructions): the others are situational — fetched by their triggering agent/skill when relevant.

## When each is needed

| Task | Required read |
|------|---------------|
| Edit any `.ux`, `manifest.json`, debug Vela framework | `vela.md` |
| Generate / iterate `release_repo/cover.png` | `poster-qc.md` |
| Touch `src/pages/about/` text styling | `conventions.md` (multi-screen width and wrapping rules) |
| Diagnose Chinese dict coverage / word-family augmentation | `dictionary-coverage.md` |
