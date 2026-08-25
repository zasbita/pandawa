# Vendored Sources

Pandawa is built on a fork of rudis. Upstream content provenance:

| Source | Local snapshot | Upstream commit | License |
|---|---|---|---|
| [sultanjulyan/rudis](https://github.com/sultanjulyan/rudis) | `C:\work\ristek\rudis` @ fork date 2026-08-25 | `6e0dbba7e455f2b2603af0cb2638d13409c0942e` | see LICENSE |

Planned future vendoring (Fase 2-5):

| Source | What is taken | Form |
|---|---|---|
| [obra/superpowers](https://github.com/obra/superpowers) | skills (TDD, brainstorming, verification-before-completion) | SKILL.md ported into `skills/` |
| [garrytan/gstack](https://github.com/garrytan/gstack) | review / QA / security-checklist methodology (no binaries, no Chromium) | SKILL.md ported into `skills/` |
| [code-yeongyu/oh-my-openagent](https://github.com/code-yeongyu/oh-my-openagent) | role-agent orchestration concepts (named agents, delegation via prompt files, context isolation) — **code NOT reused** (Bun/OpenCode-locked), concepts reimplemented host-agnostic in `agents/` + `adapters/` |

Rules:

- Never copy code verbatim from omo/gstack binaries or runtime; only methodology/checklists as markdown.
- Record the upstream commit hash here whenever content is re-synced.
- Keep upstream licenses intact when vendoring skill markdown.
