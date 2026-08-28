# Changelog

<!-- markdownlint-disable MD024 -->

All notable changes to the Pandawa CLI and templates are documented here.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [0.36.3] - 2026-08-28

### Added

- **`/pandawa.pentest` slash**: New `templates/commands/pentest.md` — agent-friendly wrapper for `pandawa pentest` (`gitleaks` + `pip-audit` + `nuclei/headers`, counts + SARIF + markdown `docs/security-reports/<date>-pentest.md` / `.pandawa/reports/`). Args `[$ARGUMENTS]` → `--url/--severity/--quick/--json/--sarif/--output`; auto-generates `pandawa.pentest.md|toml` for all agents via `create-release-packages.sh:53` (`templates/commands/*.md` loop).

## [0.36.2] - 2026-08-27

### Fixed

- **win32 PowerShell 5.1 compat**: `scripts/bash/setup-plan.sh:48` now tries `python3` → `python` → `py` (PS 5.1 often only has `python.exe`), fixes `python3 not recognized`; docs `templates/commands/ultimate.md:29` adds win32 note to avoid `head -20`/`&&` — use `Select-Object -First 20` / `; if ($?) {}`; helpers already PS 5.1 tested with LF without BOM.
- **BOM**: `scripts/powershell/update-agent-context.ps1:104` already uses `Set-Utf8NoBomLf` (LF `\n` without BOM, .NET fallback for PS 5.1) — verified, fixes `+E2 88 A9` BOM diff on every `/pandawa.plan`.

### Added

- **tasks marker automation**: New `scripts/powershell/update-tasks.ps1` + `scripts/bash/update-tasks.sh` — auto-mark `tasks.md` `- [X] T00x [done]` from `implementation-log.md` (`-FromLog`/`--from-log`) or explicit `-TaskIds T001,T002 -Status done`; PS 5.1 compat (no `head`/`&&`), LF without BOM; wired into `templates/commands/implement.md:63` checkpoint and `templates/tasks-template.md` marker note.
- **env sync**: New `scripts/powershell/sync-env-example.ps1` + `scripts/bash/sync-env-example.sh` — parse `config/services.php`/`config/*.php` `env('KEY')`, check/append `.env.example` (`-Check` CI gate, `-Fix` append), JSON mode; `templates/commands/analyze.md:114` adds Env sync check, `templates/commands/implement.md:133` runs sync on services.php changes.
- **provisional provider template**: New `templates/laravel/ProvisionalService.php.template` — Laravel service for sport without official API (MPL `id-mpl.com` scrape, futsal Wikipedia Results) with cache 3h, timeout 15s, `env()` empty → scrape branch, fallback static 9 teams; reused instead of reinventing per sport (`templates/commands/implement.md:133`, `templates/tasks-template.md`).

## [0.36.1] - 2026-08-27

### Fixed

- **`pandawa --version`**: `No such option: --version` — add global `--version`/`-V` eager flag at app callback (`src/pandawa_cli/__init__.py:1203`) printing `_pandawa_version_str()` and exiting, so `pandawa --version`/`-V` works alongside `pandawa version` subcommand; prevents TUI launch on version flag.

## [0.36.0] - 2026-08-27

### Added

- **pandawa pentest**: Free-stack integrated pentest `pandawa pentest [--url URL] [--severity low|medium|high|critical] [--json] [--output md] [--sarif sarif.json] [--quick]` — secrets (`gitleaks` or quoted-value fallback, `.env` gitignore), supply (`pip-audit` or manifest hint, floating `@main` check), active DAST (`nuclei -json` if present else security-header checks), counts `critical/high/medium/low` + `verdict`, markdown `docs/security-reports/<date>-pentest.md` / `.pandawa/reports/` auto, SARIF 2.1.0 for GitHub Code Scanning (`src/pandawa_cli/__init__.py:3449`).
- **Auto pentest on implement**: `pandawa run implement --pentest/--no-pentest --pentest-url URL --pentest-severity high` (default `--no-pentest`, threshold `high`) runs pentest after implement.

## [0.35.1] - 2026-08-27

### Fixed

- **README git.neuron.id remaining**: Replace pipeline/source badges `git.neuron.id/research/pandawa` → `github.com/zasbita/pandawa` (GitHub Actions `lint.yml`, license, source) and canonical source note `github.com/zasbita/pandawa` (`README.md:11`). Token prompt `git.neuron.id` → GitHub public no-token (optional `GITHUB_TOKEN`/`GL_TOKEN`) (`src/pandawa_cli/__init__.py:139`).

## [0.35.0] - 2026-08-27

### Fixed

- **implement checklist pipe (P1)**: `Write-Host "| Checklist | …"` pipe escaping `Missing expression after unary operator '-'` fixed via new helpers `scripts/powershell/check-checklists.ps1 -Json` + `scripts/bash/check-checklists.sh --json` that scan `FEATURE_DIR/checklists/*.md` and return `{checklists:[{file,total,completed,incomplete,status}],overall}`; `templates/commands/implement.md:2` now calls helpers instead of `Get-Content | Select-String` with raw `|`; implementation-log note adds `Set-Content -Encoding utf8NoBOM` / temp file to avoid `@"` quoting.
- **.gitignore supabase noise (P2)**: Add `supabase/.temp/` + `.supabase/` + `.temp/` (Supabase CLI `supabase link`) to `.gitignore`; `templates/commands/implement.md:4` only requires `.dockerignore` if `Dockerfile*` present (no noisy FAIL) and adds Supabase ignore pattern to common list.
- **tasks parallel [P] (P2)**: `templates/tasks-template.md:17` adds strict rule `[P]` only if different files AND no same-table/same-file dependency (e.g., `supabase/*.sql` create vs verify must be sequential) — `/pandawa.analyze` O1; adds Supabase grants split and pint `fix-before-test` hint.
- **pint gate (P2)**: `templates/commands/implement.md:8` notes `pint` fix before `pint --test` (fails on `new_with_parentheses, fully_qualified_strict_types` after generation).
- **AGENTS.md CRLF/BOM (P3)**: `scripts/powershell/update-agent-context.ps1` writes via new `Set-Utf8NoBomLf` helper (UTF-8 without BOM + LF `"\n"`), fallback via .NET `UTF8Encoding(false)` for Windows PowerShell 5.1; fixes `git diff` CRLF/BOM warning (`﻿# AGENTS.md`).

### Added

- **Supabase grants doc**: New `templates/supabase-README.md` — manual dashboard vs `npx supabase db execute --file supabase/*_grants.sql --linked` / `psql "$DATABASE_URL" -f ...`, verify via tinker, split `T00x Apply (manual)` vs `T00y Verify`; `templates/commands/implement.md:7` references it for `supabase/*_grants.sql` tasks (cannot GRANT via `SupabaseService` REST `42501`).
- **check-checklists helpers**: `scripts/bash/check-checklists.sh` + `scripts/powershell/check-checklists.ps1` (see above) included in release `scripts/` copy.

## [0.34.0] - 2026-08-27

### Added

- **pandawa qa**: New top-level `pandawa qa [--url URL] [--browser chromium|firefox|webkit] [--quick|--full] [--json] [--output report.md]` — HTTP + optional Playwright browser audit, health 0-100 rubric (console 15 + links 10 + 6 categories 75), auto-detect `localhost:3000/5173/8000/8080/5000`, link checker (cap 30), placeholder/slow detection, markdown/JSON report (`src/pandawa_cli/__init__.py:3238`).
- **Auto QA on implement**: `pandawa run implement --qa/--no-qa --qa-url --qa-browser` (default `--qa`) runs QA audit after `/pandawa.implement` and prints health verdict; skip with `--no-qa` (`src/pandawa_cli/__init__.py:5008`).

## [0.33.0] - 2026-08-27

### Fixed

- **create-new-feature param binding (P0)**: PowerShell `PositionalBinding=$false` + `FeatureDescription` `Position=0 ValueFromRemainingArguments` only; `ShortName`/`Number` named-only. Fix `Cannot convert "simpan" to Int32` when using `-ShortName 'jadwal-h-1' 'simpan jadwal H-1...'` and document `-FeatureDescription` in help (`scripts/powershell/create-new-feature.ps1:3`, `scripts/bash/create-new-feature.sh` parity).
- **Branch name truncation (P0)**: `Get-BranchName`/`generate_branch_name` keep hyphen/digit combos (`H-1`, `24h`) via `[^a-z0-9\s-]` + `[\d-]` keeper. `'simpan jadwal H-1 pertandingan mendatang'` now `simpan-jadwal-h-1` not `simpan-jadwal-h`.

### Changed

- **check-prerequisites actionable JSON (P1)**: `main`/missing `FEATURE_DIR`/`plan.md`/`tasks.md` emit `{ERROR,BRANCH,FEATURE_DIR,NEXT_STEP}` in `-Json` mode with copy-paste `create-new-feature -FeatureDescription` (PowerShell) / `--short-name` (bash); success JSON adds `FEATURE_SPEC_EXISTS/IMPL_PLAN_EXISTS/TASKS_EXISTS/TASK_COUNT/PHASE` for phase auto-detect without `-PathsOnly` (`scripts/powershell/check-prerequisites.ps1:60`, `scripts/bash/check-prerequisites.sh:82`).
- **Windows issue automation (P1)**: New `scripts/powershell/create-issues-from-tasks.ps1` + `scripts/bash/create-issues-from-tasks.sh` parse `tasks.md` `[ID][P?][USx][FR-xxx]`, `--body-file` temp file (fix PowerShell `gh issue create --body "multi line"` quoting), dedupe via `gh issue list`, throttle 0.5s, `-GroupBy story|phase` default `story` (3-5 issues Foundational/US1/US2/Polish not per T00x), `--DryRun`/`--Json`.
- **tasks-template grouping hint (P1)**: Document 3-5 Bolt grouping and script usage, keep strict `[ID][P?][USx][FR-xxx]` for `create-issues-from-tasks` + `/pandawa.analyze` (`templates/tasks-template.md:17`).
- **plan-template prune (P2)**: `setup-plan.ps1`/`setup-plan.sh` auto-detect Laravel (`composer.json`+`artisan`+`laravel`) and replace generic `Option 1/2/3` placeholder with concrete monolith tree (`templates/plan-template.md:76`).
- **Marketplace GitHub-only**: Remove `git.neuron.id` fallback (`GITLAB_MARKETPLACE_URL`) — template + marketplace fully on `github.com/zasbita/pandawa*`, local `rudis` via `--profile-path` (`src/pandawa_cli/__init__.py:334`).

## [0.32.0] - 2026-08-25

### Changed

- **GitHub-first (Opsi 2 - full migrate)**: `pandawa init` template download now fetches from `github.com/zasbita/pandawa` Releases via `api.github.com/repos/zasbita/pandawa/releases/latest` (public, no `GL_TOKEN` needed). Falls back to `git.neuron.id` only if GitHub fails, preserving internal compatibility. Added `download_template_from_github()` and GitHub-aware version check (`pandawa --version` / status).
- **Marketplace dual-host**: `_marketplace_raw_file_url()` now emits `raw.githubusercontent.com` for `github.com` URLs and `api/v4` for GitLab; `fetch_marketplace_plugins()` tries GitHub first then falls back to `git.neuron.id/research/pandawa-marketplace-tooling`. Profile archive download supports both GitHub full-repo archive and GitLab path-scoped archive with fallback.
- **Docs**: install instructions migrated to `git+https://github.com/zasbita/pandawa.git` (`uv tool install`, `uvx`) and badges/links updated; GitLab URLs retained as fallback note for internal Neuron network.
- **Logo system**: pentagon (Pandawa Lima) + rounded P + 5-dot arc with diagonal gradient, plus wordmark/horizontal lockups (`media/logo.svg`, `logo-wordmark.*`, `logo-horizontal.*`, `icon-256`, `favicon`).

## [0.31.0] - 2026-08-25

### Added (Pandawa layered architecture)

- **Skill registry (`skills/`)**: unified registry with normalized frontmatter
  (`phase` / `source` / `aliases`). 14 skills imported from superpowers
  (re-runnable via `scripts/import_superpowers.py`) plus 3 quality gates ported
  from gstack methodology-only: `code-review`, `security-audit`, `qa-audit`.
- **Role agents (`agents/`)**: Pandawa five — yudhistira-planner, bima-builder,
  arjuna-reviewer, nakula-qa, sadewa-security — with a host-agnostic delegation
  protocol (self-contained briefs, native-subagent-first dispatch, structured
  STATUS output, evidence-gated completion, context isolation).
- **`pandawa init` now installs layers**: copies bundled skills + agents into
  `.pandawa/`, and into the native skill dir for claude (`.claude/skills`) and
  opencode (`.opencode/skills`). `PANDAWA_HOME` overrides the bundled-layer root.
- **docs/architecture.md**: 4-layer model (rudis engine base, superpowers habits,
  omo-style orchestration concepts, gstack quality gates) and per-phase ownership.
- **VENDORED.md**: upstream provenance and re-sync rules.
- Tests: skill-registry contract, role-agent contract, install_layers integration.

### Changed

- Rebrand rudis → pandawa across CLI, templates, scripts, docs; new banner/tagline.

## [0.30.0] — upstream rudis snapshot

### Added

- **Operations lifecycle commands** — Pandawa now extends past the build (specify → plan → tasks → implement) into an optional operations track, aligning the toolkit with the full AI-DLC lifecycle (Inception → Construction → **Operations**):
  - **`/pandawa.deploy`**: prepares deployment automation — containerization, a CI/CD pipeline that runs the project's real checks, and environment config — following Plan-Verify-Generate. Extends an existing pipeline rather than replacing it, never writes secret values into the repo, and **never performs a live deploy** without a further explicit, specific confirmation (defaults to validated artifacts + dry-run).
  - **`/pandawa.operate`**: keeps a deployed feature healthy in three modes — Instrument (wire logs/metrics/traces/health), Detect (read user-supplied telemetry to surface ranked anomalies), and Resolve (investigate an incident root-cause and apply a scoped fix with `/pandawa.redesign`'s discipline). Treats all telemetry as untrusted data and never connects to live systems on its own.
  - **`/pandawa.postmortem`**: closes the SDD feedback loop — turns a production incident/learning into a durable amendment to the spec, NFRs, or constitution (so a fix survives the next regeneration instead of drifting away). Amends specification/governance artifacts only; never touches application source.
  - `pandawa run deploy` / `operate` / `postmortem`: CLI wrappers consistent with every other `pandawa run` subcommand; all three also surface in the TUI run pane.
  - The operations commands sit outside `/pandawa.ultimate` (which orchestrates the build phases only) — they are run on their own in a later session, when you're ready to ship and once the system is live.
- **`pandawa usage --delivery`**: AI-DLC-style delivery metrics — **predictability rate** (tasks completed vs. planned in `tasks.md`, target >80%), end-to-end **cycle time**, and per-command **phase mix**. Deliberately does not fabricate metrics that need an A/B baseline (velocity-vs-non-AI, defect-rate-normalized-to-velocity) — it reports those honestly as needing a same-work comparison instead.
- **`/pandawa.brd` command**: New command for brownfield projects that reverse-engineers a per-module Business Requirements Document breakdown from an existing codebase.
  - Surveys the repo top-down (docs, entry points, data models, auth/roles, integrations, git history) and groups findings by module (a top-level domain folder, e.g. `auth/`, `billing/`) to reconstruct business capabilities in plain language, not implementation detail.
  - Writes/updates `docs/brd/`: a system-wide `00-overview.md` (objectives, stakeholders, module index, one system diagram, dependency inventory) plus one compact **semantic-map** file per module (`modules/<slug>.md`: capabilities, entities, API surface, data flow, dependencies, test coverage) — terse and structured, not verbose prose, and far cheaper to generate and reload than a full document. Prepends a change note on re-runs instead of overwriting silently.
  - Migrates an existing single-file `docs/brd.md` from a prior version by backing it up to `docs/brd.legacy.md` and using it as reference context.
  - Flags business intent that code can't reveal with `[NEEDS CLARIFICATION]` (capped at 5 across the whole run, prioritized by impact) and resolves them with the user before finalizing.
  - Produces the background context that `/pandawa.specify` and `/pandawa.constitution` can build on for a project that didn't start with Pandawa.
  - Accepts an optional scope/focus argument to limit the survey to a specific module or area.
- **`pandawa run brd`**: CLI wrapper for `/pandawa.brd`, consistent with all other `pandawa run` subcommands.
- **`/pandawa.test` command**: New optional command that generates missing unit tests and runs SonarQube-style code quality checks.
  - Discovers your test framework (Jest, Vitest, pytest, JUnit, etc.) and naming conventions automatically
  - Identifies source files without corresponding test files, classified by priority (CRITICAL → LOW)
  - Generates missing unit tests following the project's existing patterns (happy path, edge cases, error paths)
  - SonarQube-style static analysis: code smells, duplication, complexity, maintainability, and basic security checks (hardcoded secrets, injection risks, etc.)
  - Bug detection pass: scans for functional correctness issues (off-by-one, null-handling gaps, race conditions, swallowed errors, type-coercion bugs, etc.), tries to prove each with a failing reproducing test (CONFIRMED), and falls back to a clearly-labeled SUSPECTED finding when it can't — surfaced in a dedicated Bug Report section only when bugs are found
  - Produces a quality gate report (PASSED / FAILED) with severity-classified findings, and persists it as a new timestamped file under `docs/test-reports/` on every run (never overwritten) so results can be diffed/compared over time
  - Accepts an optional path argument to scope analysis to a specific folder or module
- **`pandawa run test`**: CLI wrapper for `/pandawa.test` that invokes it via `claude --print` and captures token usage, consistent with all other `pandawa run` subcommands.
- **`pandawa profile refresh`**: Syncs the local domain profile catalog from `pandawa-marketplace-tooling`'s `profiles.json` on `main`, independent of any CLI release.
- **Domain profile versioning (visibility, not pinning)**: `profile.json` now carries a semver `version` (enforced by `pandawa-marketplace-tooling`'s validator), so a content update to a profile is no longer invisible to projects that already installed it.
  - `pandawa init --profile`/`pandawa profile update` still always fetch current `main` — there is no version pin. `version` is purely for surfacing that `main` changed.
  - Every profile install/update now records `{version, ref, source, installed_at}` for that profile in a new per-project `.pandawa/profile-lock.json`, read from the just-extracted `profile.json` (not the possibly-stale catalog cache).
  - **`pandawa profile status`**: compares this project's locked profile version(s) against the live catalog and flags "update available".
  - **`pandawa profile update <key>`**: re-fetches a profile already installed in this project (same content path as `init --profile`, scoped to one profile), auto-detecting `--ai` from whichever agent instruction file the project already has.
  - `pandawa profile list` gained a Version column; the TUI's Profiles pane mirrors it, and the Status pane shows the current project's installed profile version plus an "update available" indicator (mirroring the existing CLI-self-update row).

### Changed

- **`/pandawa.brd` rewritten to a lean semantic map** (was a verbose 3-file-per-module BRD): now emits one terse `modules/<slug>.md` per module (capabilities, entities, API surface, data flow, dependencies, test coverage) instead of separate `brd.md` + `flow.md` + `technical.md`, cutting token cost substantially while aligning with AI-DLC's "semantic map" for brownfield navigation. Consolidates the three old per-module templates into `templates/brd-module-template.md`, migrates old-layout docs in place, and updates `/pandawa.redesign`'s brownfield fallback to read the single map file.
- **Mimicry Principle** added to `/pandawa.implement` and `/pandawa.redesign`: in an existing codebase the agent must find the nearest existing example (controller, service, error handler, logger, auth guard) and mimic its structure/naming/conventions rather than generating from a blank-slate description — producing code that fits the project and passes the parity/architecture gates more reliably.
- **Bolts (iteration units)** added to `/pandawa.tasks` and `tasks-template.md`: each user-story phase is framed as a Bolt — a short, one-session, independently testable increment ending at a checkpoint — with guidance to split oversized stories into ordered sub-Bolts so work stays shippable at every step.
- **AI-DLC alignment documented** in `spec-driven.md`: new "Beyond the Build: Operations & Continuous Feedback" and "Working Principles for AI Collaboration" (semantic context, mimicry, Bolts, adaptive depth, human oversight) sections.
- **Frontend generation quality (`tmforum-oda`)**: the frontend agent prompt now loads the real design-system pattern doc + canonical example page (the old path pointed at a non-existent `templates/frontend-module/`), and both the example page and `frontend-pattern.md` now embody the FE-011 visual standard (stat/KPI row, rich empty state, shaped skeleton, accent anchor, tokens-only) so "copy the reference" yields polished pages instead of bare ones. Kept in sync across the profile and the `tmf-oda-constitution` plugin copy.
- **UI/UX is now a first-class pipeline input**: `spec-template.md` gains a "UI/UX & Screens" section (screen inventory, per-screen states, interactions, design reference); `/pandawa.specify` exempts UI/UX intent from the no-implementation-detail rule and surfaces invented assumptions for confirmation; `/pandawa.plan` carries it forward; `/pandawa.implement` builds screens to that intent. The `Pass B` visual gate gained a concrete "offside" checklist and Module-Federation render guidance, and a static FE-011 linter enforces the visual rules even in headless/CI runs.
- **Requirement traceability by ID**: tasks cite `[FR-###]` and every FR maps to ≥1 task; `/pandawa.analyze` maps coverage by spec ID (plus Success Criteria) and treats an uncovered `FR-###`/`SC-###` as a hard blocker; `/pandawa.implement` re-checks coverage as a precondition and reports per-requirement completion evidence.
- **`pandawa` CLI startup & command latency**: the profile-catalog auto-refresh is throttled by a short TTL and fetches each profile concurrently instead of serially, and the shared HTTP client is built lazily instead of at import — noticeably faster commands with no change to generated output. `pandawa profile refresh` still always fetches.
- **Token thrift**: `/pandawa.ultimate` no longer re-reads documents already in context, and the per-phase verification gate plus `/pandawa.test` compress tool output and print compact summaries.
- **Domain profiles (`tmforum-oda`, `tmforum-oda-door-v3`) moved to `pandawa-marketplace-tooling`**: profile content now lives in that repo's `profiles/<id>/` (registered in its root `profiles.json`), alongside skill/agent plugins, instead of this repo's `templates/tm-forum-oda-*`. One contribution flow, one CI validation job, one `CODEOWNERS` gate for both plugins and profiles.
  - `pandawa init --profile <id>` fetches a profile's folder live via GitLab's repository-archive API — no CLI release or packaging step in either repo, and profile content is available the moment a change merges to `pandawa-marketplace-tooling`'s `main`.
  - `pandawa profile list`/`set-local` now do a best-effort catalog refresh first, so newly-published profiles are recognized without waiting for a CLI release.
  - `--profile-path` now fully bypasses the catalog check (useful for authoring/testing a profile that hasn't merged yet).
  - Adding a new profile is fully self-service: a `profiles/<id>/profile.json` folder plus one `{"id", "path"}` entry in `pandawa-marketplace-tooling`'s `profiles.json` — see that repo's `CONTRIBUTING.md`.

### Fixed

- **Governance-guard hook failed on macOS**: the `PreToolUse`/`SessionStart` hook written into `.claude/settings.json` invoked a bare `python`, which doesn't exist on macOS (only `python3`) — every tool call logged `python: command not found` and the guard silently never ran (fail-open). The hook now resolves `python3`/`python` at runtime on POSIX (Windows keeps `python`) and auto-migrates any project's stale/buggy hook on the next `pandawa` run.
- **macOS / bash 3.2 script bugs**: `update-agent-context.sh` no longer aborts under `set -e` when re-running on an already-populated agent file (`((count++))` → `$((count+1))`) and escapes sed replacement text correctly (no more `&`-injection or leaked backslashes); `create-new-feature.sh` no longer uses the bash-4-only `${word^^}`.
- **sh/ps script parity & JSON robustness**: `HAS_GIT` is emitted as a JSON boolean in both variants (and is present in both `create-new-feature` outputs); the PowerShell `AVAILABLE_DOCS` is always a JSON array (was `null`/scalar for 0/1 docs on PS 5.1); bash JSON emitters escape interpolated path values.
- **Scaffold gaps that undercut the new gates**: `tasks-template.md` now carries the `[FR-###]` citation slot, `plan-template.md` gains the "UI/UX & Screens (carried from spec)" section, and `spec-template.md` gains a Non-Functional Requirements subsection.
- **CLI robustness**: `pandawa init` no longer crashes on a `settings.json` that is valid JSON but not an object (`[]` / `null`); the shell-profile token reader's `.lstrip("export ")` (a character-set strip) is corrected to `.removeprefix(...)`.
- **Marketplace validator** now also flags on-disk plugins/profiles that lack a registration entry (previously only registered-→-on-disk was checked).
- **`pandawa init --profile <id>` generated wrong onboarding text for any profile other than `tmforum-oda`**: the `CLAUDE.md`/`AGENTS.md` block and `.pandawa/memory/constitution.md` seed were hardcoded to `tmforum-oda`'s specific domain numbering, stack (React, CQRS, TMF Open API), and filenames (`_oda-compliance-matrix.json`, `_adherence.oxlintrc.json`, `04-frontend-engineering.md`) — installing a different profile (e.g. the new `pegadaian` profile) still produced instructions describing TM Forum ODA/React, regardless of the actual profile's content.
  - Both blocks are now built by inspecting the extracted profile directory: the compliance-artifact reference falls back from `_oda-compliance-matrix.json` to a generic `validation/*.md` rule-book pointer when the former isn't present; the frontend-constitution file reference is located by pattern (`constitution/*frontend*.md`) instead of a fixed filename; the hardcoded 6-row domain table is replaced with a pointer to the profile's own `constitution/00-index.md` (which is authoritative and complete, unlike the old table that only ever covered 6 of `tmforum-oda`'s 15 domains).
  - Verified against real `pandawa init --profile <id>` runs for all three published profiles (`pegadaian`, `tmforum-oda`, `tmforum-oda-door-v3`) — no regression in `tmforum-oda`'s output, `pegadaian` now gets correct instructions.

### Removed

- Profile release packaging (`build_profile` in `create-release-packages.sh`/`.ps1`, the `pandawa-profile-*.zip` release assets, and the static per-profile entries in `.gitlab-ci.yml`'s release job) — no longer needed now that profiles are fetched live instead of shipped as release artifacts.

## [0.2.0] - 2026-06-22

### Added

- **Plugin marketplace bridge**: `pandawa init --ai claude` now registers the private Pandawa plugin marketplace in the project's `.claude/settings.json` (`extraKnownMarketplaces`) and enables the baseline `pandawa-core` plugin (`enabledPlugins`). Skills and agents are distributed via Claude Code `/plugin` — PANDAWA points to the marketplace, it does not bundle plugin content.
  - Version-controlled `.claude/settings.json` means teammates are prompted to install on trusting the folder; no manual `/plugin` commands needed.
  - `--marketplace-url` (or `PANDAWA_MARKETPLACE_URL`) overrides the marketplace URL; `--no-marketplace` opts out. Non-Claude assistants are skipped (the mechanism is Claude Code-specific).
  - Authentication reuses the existing `GL_TOKEN` / `GITLAB_TOKEN`.
- **Baseline guardrails (Claude)**: `pandawa init` writes a loose, deny-first permission set to `.claude/settings.json` — denies only clearly-dangerous actions (e.g. `rm -rf`, `git push --force`, reading/writing `.env`/secrets) and leaves everything else at default. Unions with any existing `permissions.deny`. Opt out with `--no-guardrails`.
- **Project-context starter**: `pandawa init` scaffolds a `CLAUDE.md` template (never overwrites an existing one) to capture project context for agents. Opt out with `--no-claude-md`.
- Updated TM Forum ODA reusable design system template with new MCS app bootstrap files (`App.tsx`, `bootstrap.tsx`, `index.tsx`, `setupTests.ts`, etc.) for standalone MFE structure.

## [0.1.0] - 2026-06-17

### Added

- Added system architecture diagram to documentation.

### Changed

- Updated system diagram to reflect current architecture.

## [0.0.22] - 2025-11-07

- Support for VS Code/Copilot agents, and moving away from prompts to proper agents with hand-offs.
- Move to use `AGENTS.md` for Copilot workloads, since it's already supported out-of-the-box.
- Adds support for the version command. ([#486](https://git.neuron.id/research/pandawa/issues/486))
- Fixes potential bug with the `create-new-feature.ps1` script that ignores existing feature branches when determining next feature number ([#975](https://git.neuron.id/research/pandawa/issues/975))
- Add graceful fallback and logging for GitHub API rate-limiting during template fetch ([#970](https://git.neuron.id/research/pandawa/issues/970))

## [0.0.21] - 2025-10-21

- Fixes [#975](https://git.neuron.id/research/pandawa/issues/975) (thank you [@fgalarraga](https://github.com/fgalarraga)).
- Adds support for Amp CLI.
- Adds support for VS Code hand-offs and moves prompts to be full-fledged chat modes.
- Adds support for `version` command (addresses [#811](https://git.neuron.id/research/pandawa/issues/811) and [#486](https://git.neuron.id/research/pandawa/issues/486), thank you [@mcasalaina](https://github.com/mcasalaina) and [@dentity007](https://github.com/dentity007)).
- Adds support for rendering the rate limit errors from the CLI when encountered ([#970](https://git.neuron.id/research/pandawa/issues/970), thank you [@psmman](https://github.com/psmman)).

## [0.0.20] - 2025-10-14

### Added

- **Intelligent Branch Naming**: `create-new-feature` scripts now support `--short-name` parameter for custom branch names
  - When `--short-name` provided: Uses the custom name directly (cleaned and formatted)
  - When omitted: Automatically generates meaningful names using stop word filtering and length-based filtering
  - Filters out common stop words (I, want, to, the, for, etc.)
  - Removes words shorter than 3 characters (unless they're uppercase acronyms)
  - Takes 3-4 most meaningful words from the description
  - **Enforces GitHub's 244-byte branch name limit** with automatic truncation and warnings
  - Examples:
    - "I want to create user authentication" → `001-create-user-authentication`
    - "Implement OAuth2 integration for API" → `001-implement-oauth2-integration-api`
    - "Fix payment processing bug" → `001-fix-payment-processing`
    - Very long descriptions are automatically truncated at word boundaries to stay within limits
  - Designed for AI agents to provide semantic short names while maintaining standalone usability

### Changed

- Enhanced help documentation for `create-new-feature.sh` and `create-new-feature.ps1` scripts with examples
- Branch names now validated against GitHub's 244-byte limit with automatic truncation if needed

## [0.0.19] - 2025-10-10

### Added

- Support for CodeBuddy (thank you to [@lispking](https://github.com/lispking) for the contribution).
- You can now see Git-sourced errors in the Pandawa CLI.

### Changed

- Fixed the path to the constitution in `plan.md` (thank you to [@lyzno1](https://github.com/lyzno1) for spotting).
- Fixed backslash escapes in generated TOML files for Gemini (thank you to [@hsin19](https://github.com/hsin19) for the contribution).
- Implementation command now ensures that the correct ignore files are added (thank you to [@sigent-amazon](https://github.com/sigent-amazon) for the contribution).

## [0.0.18] - 2025-10-06

### Added

- Support for using `.` as a shorthand for current directory in `pandawa init .` command, equivalent to `--here` flag but more intuitive for users.
- Use the `/pandawa.` command prefix to easily discover Pandawa-related commands.
- Refactor the prompts and templates to simplify their capabilities and how they are tracked. No more polluting things with tests when they are not needed.
- Ensure that tasks are created per user story (simplifies testing and validation).
- Add support for Visual Studio Code prompt shortcuts and automatic script execution.

### Changed

- All command files now prefixed with `pandawa.` (e.g., `pandawa.pandawa.md`, `pandawa.plan.md`) for better discoverability and differentiation in IDE/CLI command palettes and file explorers

## [0.0.17] - 2025-09-22

### Added

- New `/clarify` command template to surface up to 5 targeted clarification questions for an existing spec and persist answers into a Clarifications section in the spec.
- New `/analyze` command template providing a non-destructive cross-artifact discrepancy and alignment report (spec, clarifications, plan, tasks, constitution) inserted after `/tasks` and before `/implement`.
  - Note: Constitution rules are explicitly treated as non-negotiable; any conflict is a CRITICAL finding requiring artifact remediation, not weakening of principles.

## [0.0.16] - 2025-09-22

### Added

- `--force` flag for `init` command to bypass confirmation when using `--here` in a non-empty directory and proceed with merging/overwriting files.

## [0.0.15] - 2025-09-21

### Added

- Support for Roo Code.

## [0.0.14] - 2025-09-21

### Changed

- Error messages are now shown consistently.

## [0.0.13] - 2025-09-21

### Added

- Support for Kilo Code. Thank you [@shahrukhkhan489](https://github.com/shahrukhkhan489) with [#394](https://git.neuron.id/research/pandawa/pull/394).
- Support for Auggie CLI. Thank you [@hungthai1401](https://github.com/hungthai1401) with [#137](https://git.neuron.id/research/pandawa/pull/137).
- Agent folder security notice displayed after project provisioning completion, warning users that some agents may store credentials or auth tokens in their agent folders and recommending adding relevant folders to `.gitignore` to prevent accidental credential leakage.

### Changed

- Warning displayed to ensure that folks are aware that they might need to add their agent folder to `.gitignore`.
- Cleaned up the `check` command output.

## [0.0.12] - 2025-09-21

### Changed

- Added additional context for OpenAI Codex users - they need to set an additional environment variable, as described in [#417](https://git.neuron.id/research/pandawa/issues/417).

## [0.0.11] - 2025-09-20

### Added

- Codex CLI support (thank you [@honjo-hiroaki-gtt](https://github.com/honjo-hiroaki-gtt) for the contribution in [#14](https://git.neuron.id/research/pandawa/pull/14))
- Codex-aware context update tooling (Bash and PowerShell) so feature plans refresh `AGENTS.md` alongside existing assistants without manual edits.

## [0.0.10] - 2025-09-20

### Fixed

- Addressed [#378](https://git.neuron.id/research/pandawa/issues/378) where a GitHub token may be attached to the request when it was empty.

## [0.0.9] - 2025-09-19

### Changed

- Improved agent selector UI with cyan highlighting for agent keys and gray parentheses for full names

## [0.0.8] - 2025-09-19

### Added

- Windsurf IDE support as additional AI assistant option (thank you [@raedkit](https://github.com/raedkit) for the work in [#151](https://git.neuron.id/research/pandawa/pull/151))
- GitHub token support for API requests to handle corporate environments and rate limiting (contributed by [@zryfish](https://github.com/@zryfish) in [#243](https://git.neuron.id/research/pandawa/pull/243))

### Changed

- Updated README with Windsurf examples and GitHub token usage
- Enhanced release workflow to include Windsurf templates

## [0.0.7] - 2025-09-18

### Changed

- Updated command instructions in the CLI.
- Cleaned up the code to not render agent-specific information when it's generic.

## [0.0.6] - 2025-09-17

### Added

- opencode support as additional AI assistant option

## [0.0.5] - 2025-09-17

### Added

- Qwen Code support as additional AI assistant option

## [0.0.4] - 2025-09-14

### Added

- SOCKS proxy support for corporate environments via `httpx[socks]` dependency

### Fixed

N/A

### Changed

N/A
