# Role Agents — Orchestration Layer (L3)

Five named roles (Pandawa). Each role = a self-contained prompt definition that any
host can run as a subagent or a fresh headless session.

| Role | Phase | Gate skills | Analogy |
|---|---|---|---|
| [yudhistira-planner](yudhistira-planner.md) | plan | — (uses rudis plan templates + brainstorming skill) | judges, plans |
| [bima-builder](bima-builder.md) | implement | test-driven-development, verification-before-completion | executes |
| [arjuna-reviewer](arjuna-reviewer.md) | review | code-review | precision |
| [nakula-qa](nakula-qa.md) | verify | qa-audit | first twin |
| [sadewa-security](sadewa-security.md) | review | security-audit | second twin |

## Delegation protocol

The orchestrator (host main session, or `pandawa run` wrapper):

1. **Assign**: pick the role whose phase matches the current rudis lifecycle phase.
   One role active per phase; reviewer and security may both run at `review`.
2. **Brief**: render a self-contained prompt file:
   `task goal + relevant artifacts (spec/plan/task text) + role definition + gate skill`.
   The executor must NOT need the orchestrator's conversation history.
3. **Dispatch**:
   - Host has native subagents (Claude Code Task tool, OpenCode task tool) → dispatch natively.
   - Otherwise → spawn headless CLI session (`claude -p`, `opencode run`, `codex exec`,
     `gemini -p`, ...) with the prompt file. Adapter table maps host → command.
4. **Collect**: executor returns structured output:
   `STATUS: DONE | DONE_WITH_CONCERNS | BLOCKED | NEEDS_CONTEXT`, plus findings/artifacts.
5. **Gate**: review-phase roles attach their gate skill output to the task record.
   Builder claims are never trusted without the matching gate evidence.

## Context isolation rules

- Executor sees its brief only — never sibling reasoning (prevents QA biasing toward
  "confirming" the builder).
- Review/security roles always receive diff/artifacts directly from disk, not
  summaries written by the builder.
- Failed attempt output is fed back into the retry brief (bounded retries, then
  escalate to human).

## File format

Each `<role>.md`: frontmatter (`name`, `phase`, `skills`, `model-hint`) + body =
system prompt for that role. Bodies stay host-neutral markdown.
