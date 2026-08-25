---
name: "qa-audit"
description: "Report-only QA audit of a running app or a feature branch. Console errors, broken links, visual/functional/UX/content/performance/accessibility scoring, health score 0-100. No fixes."
phase: verify
source: gstack
aliases: ["gstack:qa-only", "qa report"]
---

# QA Audit Gate

Systematic QA of the app under test. Report-only — findings, evidence, health score.
(Fix loop is a separate concern; this gate never mutates code.)

## Mode selection

- **Diff-aware** (feature branch, no URL given): derive test focus from the branch diff — changed routes/components get deep testing, rest smoke-level.
- **Full**: URL provided → test whole app.
- **Quick**: critical/high checks only.

## Workflow

1. **Initialize**: confirm app reachable (or start dev server per project convention). Note build/deploy state.
2. **Orient**: enumerate entry points (routes/nav). List them before diving in.
3. **Explore per page/flow**:
   - Console: errors and warnings (errors weigh heavily).
   - Network: failed requests, 4xx/5xx, slow calls >2s.
   - Functional: forms submit, buttons act, empty/error/loading states render.
   - Visual: layout breaks at mobile/tablet/desktop widths; overlapping/truncated content.
   - Content: placeholder text ("Lorem", TODO), wrong labels, dead links.
   - Accessibility basics: keyboard reachability of primary actions, missing alt text, unlabeled form inputs, contrast failures on key text.
4. **Document each finding**: severity + repro steps + screenshot/evidence where host tooling allows.
5. **Wrap up**: health score + ship-readiness verdict.

## Health score rubric (0–100)

- Console errors: weight 15 — clean=15, warnings only=10, errors=0–5.
- Links: weight 10 — % working.
- Six categories (visual, functional, UX, content, performance, accessibility): weight 75 total, scored per category from findings density and severity.

Verdict bands: 90+ ship-ready · 70–89 minor fixes · 50–69 not ready · <50 broken.

## Host tooling note

Use whatever browser automation the host provides (native browser tools, Playwright,
MCP browser servers). If no browser tooling exists, degrade to code-level QA: static
checks of routes/handlers, error boundaries, loading states, and a written manual test
plan — say so explicitly in the report header.

## Output

```
QA Audit: health 78/100 (minor fixes)
CRITICAL: ...
HIGH: ...
MEDIUM: ...
LOW/cosmetic: ...
Tested: <pages/flows>, Skipped: <what and why>
```

Every claim carries evidence. No fix suggestions required, but one-line fix hints are welcome.
