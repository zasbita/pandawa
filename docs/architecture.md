# Pandawa Architecture

Pandawa = spec-driven agentic toolkit. Four layers, one owner per concern.

```
L4 QUALITY GATES    port of gstack methodology      review, QA, security checklist
L3 ORCHESTRATION    omo concepts, host-agnostic     role agents, delegation, context isolation
L2 HABITS           superpowers skills              TDD, brainstorming, verification
L1 ENGINE/BASE      rudis fork (this CLI)           constitution -> specify -> plan -> tasks -> implement
```

## Ownership rules (conflict resolution)

gstack and omo are *totalizing* — they want the whole workflow. Pandawa prevents
role conflict by giving each layer exactly one job:

| rudis lifecycle phase | Active layer | Content |
|---|---|---|
| constitution / specify | L1 only | pure rudis templates |
| plan | L2 pre-step | superpowers Socratic brainstorming before planning |
| tasks | L3 | split tasks -> assign role agent |
| implement | L2 habits | TDD RED-GREEN-REFACTOR, subagent-driven dev |
| verify / review | L4 gates | review, QA, security checklist |

Duplicate skills across upstreams resolve to **one canonical skill** in `skills/`;
others become aliases in the registry metadata.

## Directory contract

```
src/pandawa_cli/   CLI core (forked from rudis) — init, templates, agent adapters
templates/         lifecycle artifacts (spec, plan, tasks, checklist)
skills/            unified skill registry; each skill = SKILL.md + frontmatter metadata
agents/            role-agent definitions (planner / builder / reviewer / qa twins)
adapters/          per-host install logic notes; code lives in src (AGENT_CONFIG)
docs/              architecture + guides
tests/             pytest suite
```

## Multi-host strategy

`pandawa init --ai <agent>` already generates per-host command files for 17 agents
(see AGENTS.md table). Skills and role agents follow the same pattern: one canonical
markdown source, rendered into each host's native location/format by the adapter.

Role-agent delegation protocol:

- Host with native subagent support (Claude Code Task tool, OpenCode task tool):
  use native subagents.
- Other hosts: fallback = spawn a fresh headless session with a self-contained
  prompt file (karsa-style context projection). The prompt file is the interface.

## Token discipline

Skills load on demand (progressive disclosure, superpowers-style). Nothing loads
all skills into context.
