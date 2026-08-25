---
description: Render local delivery, task, checkpoint, and audit report
---

## User Input

```text
$ARGUMENTS
```

Produce a factual local delivery report. Do not invent metrics.

1. Find active `specs/*/tasks.md` and root `tasks.md`; count total, done, pending,
   running, and failed tasks. Include task IDs for non-done items.
2. Read `implementation-log.md` and `.pandawa/audit.log` when present. Summarize
   latest checkpoint, task transitions, failures, command durations, and token/cost
   fields that actually exist.
3. Report dependency blockers and parallel tracks that are ready. Flag stale
   `[running]` tasks older than the latest recorded session; do not silently reset.
4. Output compact Markdown with sections: Status, Tasks, Recovery, Audit, Evidence.
   Every claim cites a file path or says `not available`.

For a machine-readable report, emit the same data as JSON after the Markdown only
when `$ARGUMENTS` contains `--json`.
