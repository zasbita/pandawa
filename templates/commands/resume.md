---
description: Resume implementation from persisted task and checkpoint state
---

## User Input

```text
$ARGUMENTS
```

Resume current feature without restarting completed work.

1. Locate active `tasks.md`. Read it, `plan.md`, `spec.md`, and
   `implementation-log.md` if present. Resolve repository root once.
2. Treat `[X]` or `[done]` tasks as complete. Treat missing markers and `[pending]`
   as pending. Treat `[running]` as interrupted: inspect its log entry and working
   tree before deciding whether to continue or reset it to `[pending]`.
3. Treat `[failed]` as the first recovery target. Read its recorded error, run the
   smallest reproducer, and retry at most 3 times. After that, stop and ask for
   human input. Never loop indefinitely.
4. Verify prerequisites before claiming next task. Select first ready task in
   dependency order, or delegate independent ready tasks using `/pandawa.parallel`.
5. Before each task mark `[running]`; after verification mark `[done]` or `[failed]`.
   Append task ID, files, result, and verification command to
   `implementation-log.md`. Do not rewrite completed history.
6. At end print checkpoint, completed tasks, remaining tasks, failures, and exact
   next command. Never claim feature complete while any required task is pending
   or failed.
