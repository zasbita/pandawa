# Cross-Agent UX Consistency

> **Status:** Analysis + architecture decision. What ships today: the `/pandawa`
> concierge entry point (cross-agent) and SDD (already cross-agent). Capabilities
> beyond SDD remain in the marketplace and are **install-first** — see "Decision" and
> "Open problem" below.

## 1. Context

Base Pandawa already delivers a **consistent Spec-Driven Development UX across all 16
supported agents**: the same `/pandawa.*` commands behave the same everywhere, achieved
with one durable paradigm — **slash command + script + file-based state**.

The newer capabilities (the TM Forum ODA constitution framework, document/factory skills)
live in the separate **pandawa marketplace** (`tmf-oda-constitution`, `docs-pack`, `pandawa-core`)
and are installed via Claude Code's `/plugin` — a Claude-only mechanism.

**Question:** can the *user experience* be made consistent across all agents, while
respecting the project's architecture — capabilities stay in the marketplace and are
**installed first**, never bundled into core Pandawa?

## 2. Core principles

1. **Distribution/runtime != capability content.** Capabilities are prompt markdown +
   scripts. Claude's plugin system is one delivery mechanism, not the capability.
2. **UX parity != enforcement parity.** The experience can be identical; the guarantee
   behind a gate differs by runtime (strongest on Claude).
3. **Capabilities belong in the marketplace, install-first.** Core Pandawa ships only SDD
   and the `/pandawa` entry point. Delivery, documents, and the skill/agent factory are
   marketplace packs you install on demand. **Core never bundles a capability** — doing
   so would duplicate the marketplace and break the install-first contract.

## 3. What is portable vs Claude-only

| Layer | Cross-agent? | Why |
|-------|--------------|-----|
| SDD commands `/pandawa.*` | Yes (all 16 agents) | Generated per-agent by packaging |
| `/pandawa` concierge router | Yes | It is just a command/prompt |
| Marketplace `/plugin install` | No (Claude only) | Claude Code feature |
| Skill auto-trigger, subagents | No (Claude only) | Claude Code runtime |
| Hooks + deny-first permissions (enforcement) | No (Claude only) | Claude Code settings |

So the *delivery and enforcement* of marketplace capabilities is Claude-specific. The
*content* is portable in principle, but must still be delivered install-first, not
bundled.

## 4. Decision

- **Keep capabilities in the marketplace, install-first.** Do **not** add core
  commands like `/pandawa.deliver` or `/pandawa.doc` — those duplicate `tmf-oda-constitution` /
  `docs-pack` and violate the install-first contract.
- **Ship a cross-agent `/pandawa` concierge.** It routes to the always-present SDD
  commands on any agent, and — on Claude — to *installed* marketplace packs. When a
  capability's pack is not installed, the router gives the install command and stops; it
  never bundles a substitute.
- **Consequence:** on non-Claude agents, only SDD is available today, because
  the marketplace installs on Claude. Cross-agent capability parity is therefore an
  open problem (next section), not something to fake by bundling.

## 5. Open problem: cross-agent install of marketplace capabilities

`/plugin` is Claude-only, so non-Claude agents currently cannot install marketplace
capabilities. Two ways to close the gap *without* bundling into core:

- **Option A — marketplace command-export + a Pandawa install step.** The marketplace
  additionally publishes command-form versions of a capability (e.g. an ODA delivery
  FSM command, a document-helper command). A Pandawa CLI step (`pandawa add <pack>` or
  similar) fetches those command files from the marketplace and writes them into the
  project's per-agent command folder. This keeps capabilities in the marketplace, keeps
  install-first, and works on any agent — the runtime difference (FSM-in-a-command vs
  subagents/skills) stays hidden, the UX stays consistent.
- **Option B — keep capabilities Claude-only.** Accept that delivery/documents/factory
  require Claude Code; non-Claude agents get SDD + the router only.

Option A is the path to true cross-agent UX while honoring install-first. It is a
**marketplace-side** change (plus a small CLI install command), explicitly **not** a
core bundling change. It is not yet implemented.

## 6. What ships today

- `templates/commands/pandawa.md` -> `/pandawa` concierge, generated for **all** agents
  (the Claude-only packaging skip was removed; the Copilot companion-prompt glob was
  widened to include the root entry; the "missing script" warning now fires only for
  commands that reference `{SCRIPT}`). The router is install-first and degrades to SDD
  only when no marketplace packs are present / on non-Claude agents.
- SDD commands and the marketplace (`tmf-oda-constitution`, `docs-pack`, `pandawa-core`) are
  **unchanged**.

## 7. Enforcement & provisioning (unchanged by this work)

- **Enforcement strength** — strongest on Claude (subagents, hooks, deny-first
  permissions). Any portable FSM (Option A) would enforce gates at the prompt level
  only. (Prose is not the safety mechanism — rely on mechanical guardrails.)
- **Provisioning** — Claude installs dynamically via `/plugin`; a cross-agent install
  (Option A) would fetch from the marketplace at a deliberate `add` step.

Neither affects the daily SDD + concierge UX, which is identical across agents today.
