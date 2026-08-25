---
description: Analyze tasks.md dependency graph and dispatch independent task tracks to host subagents
---

## User Input

```text
$ARGUMENTS
```

Run a bounded parallel implementation pass over the current feature.

1. Locate the active `specs/*/tasks.md` (or root `tasks.md`). If none exists, stop
   and tell the user to run `/pandawa.tasks`.
2. Read the complete `tasks.md`, `plan.md`, `spec.md`, and `implementation-log.md`
   when present. Parse task IDs, `[P]`, explicit `depends on` text, phase order,
   and runtime markers. Never infer independence merely because two tasks mention
   different files: shared symbols, migrations, APIs, and tests remain dependent.
3. Build dependency tracks. Put only genuinely independent tasks in the same
   track. Preserve phase and prerequisite order. Exclude `done` tasks; isolate
   `failed` tasks until their prerequisite fix is understood.
4. Show a compact plan:

   ```text
   Track A: T012, T013
   Track B: T014 (depends on T012, T013)
   Blocked: T015 (depends on T014)
   ```

5. Ask for confirmation before modifying files. On confirmation, dispatch each
   ready track through the host's native subagent mechanism (Task tool, team mode,
   or equivalent). Do not assume a specific host API. If no subagent mechanism is
   available, execute tracks sequentially and say so.
6. Each worker MUST claim its task by changing its marker to `[running]`, work only
   within task scope, run the smallest relevant verification, then mark `[done]` or
   `[failed]` and append one line to `implementation-log.md`.
7. Coordinator waits for all current tracks, reports failures, and unlocks the next
   wave only after prerequisites pass. Never run more than one worker on same file.

Concurrency is bounded by available host workers and the explicit user limit in
`$ARGUMENTS` (default: 3). No infinite retry. Escalate unresolved conflicts to user.
