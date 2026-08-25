---
name: "code-review"
description: "Pre-landing diff review: SQL/data safety, race conditions, LLM trust boundaries, shell injection, enum completeness, plus informational pass. Fix-first with confidence calibration."
phase: review
source: gstack
aliases: ["gstack:review", "superpowers:requesting-code-review"]
---

# Code Review Gate

Review the branch diff against the base branch for structural issues tests don't catch.

## Step 0 — Base branch & scope

1. Detect base branch (`origin/HEAD`, else main/master). On base branch with no diff → stop: nothing to review.
2. **Scope drift check first**: state the intent (plan/tasks doc/commit messages), then compare files changed vs intent. Report `Scope Check: CLEAN | DRIFT DETECTED | REQUIREMENTS MISSING` before anything else.

## Step 1 — Read the FULL diff before commenting

Never flag issues already addressed in the diff. Skip anything fine. Only real problems.

## Step 2 — Two-pass review

### Pass 1 — CRITICAL

- **SQL & Data Safety**: string interpolation in SQL → parameterized queries; TOCTOU check-then-set → atomic `WHERE`; bypassing model validations on direct DB writes; N+1 missing eager loading.
- **Race Conditions**: find-or-create without unique index; status transitions without atomic `WHERE old_status = ? UPDATE`; read-check-write without uniqueness constraint.
- **LLM Output Trust Boundary**: LLM-generated values persisted without format validation (email/URL regex); structured tool output accepted without shape checks; LLM URLs fetched without allowlist (SSRF); LLM output stored in knowledge bases unsanitized (stored prompt injection).
- **Shell Injection**: `shell=True` + interpolation in subprocess calls → argument arrays; `os.system()` with variables; `eval()`/`exec()` on generated code.
- **Enum & Value Completeness** (requires reading OUTSIDE the diff): new enum/status/tier value → grep sibling values, READ every consumer that switches/filters/displays on them, flag unhandled cases; check allowlists and `case/if-elsif` fall-throughs.
- Unsafe HTML rendering of user data (`.html_safe`, `dangerouslySetInnerHTML`, `v-html`, `|safe`) → XSS.

### Pass 2 — INFORMATIONAL

- Async/sync mixing (sync IO inside `async def`, `time.sleep` in async).
- Column/field name safety vs actual schema.
- LLM prompt issues (0-indexed lists, tool lists drifting from wiring).
- Completeness gaps (shortcut where full version <30 min; missing negative-path tests mirroring happy-path).
- Time-window safety (date-key assumptions, mismatched bucketing).
- Type coercion at serialization boundaries (hash/digest input normalization).
- View/frontend O(n*m) lookups; filtering in app code that belongs in a WHERE clause.
- CI/CD changes: version consistency across VERSION/tags/publish scripts, secrets via secret refs not hardcoded, publish idempotency.

## Step 3 — Confidence calibration

Every finding carries `(confidence: N/10)`:

| Score | Rule |
|---|---|
| 9–10 | Verified by reading specific code — show |
| 7–8 | Strong pattern match — show |
| 5–6 | Could be FP — show with caveat |
| 3–4 | Suppress from report, appendix only |
| 1–2 | Speculation — only if P0 |

Before emitting: re-read the cited lines and confirm the field/function exists. Kills false positives.

## Step 4 — Fix-first output

```
Pre-Landing Review: N issues (X critical, Y informational)

AUTO-FIXED:
- [file:line] problem → fix applied   (obvious mechanical fixes only)

NEEDS INPUT:
- [file:line] problem
  Recommended fix: ...
```

Ambiguous items batched into one user question. Never commit/push/PR — that is the ship step's job. Be terse: one line problem, one line fix.
