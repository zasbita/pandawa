<div align="center">
    <img src="./media/logo_large.png" alt="Pandawa Logo" width="200" height="200"/>
    <h1>Pandawa</h1>
    <h3><em>Build high-quality software faster.</em></h3>
</div>

<p align="center">
    <strong>Open-source toolkit that helps you focus on product scenarios and predictable outcomes — not vibe-coding everything from scratch.</strong>
</p>

<p align="center">
    <a href="https://git.neuron.id/research/pandawa/-/pipelines"><img src="https://git.neuron.id/research/pandawa/badges/main/pipeline.svg" alt="Pipeline"/></a>
    <a href="https://git.neuron.id/research/pandawa/blob/main/LICENSE"><img src="https://img.shields.io/badge/license-MIT-blue" alt="License"/></a>
    <a href="https://git.neuron.id/research/pandawa"><img src="https://img.shields.io/badge/source-git.neuron.id-orange" alt="Source"/></a>
</p>

---

## Table of Contents

- [🤔 What is Spec-Driven Development?](#-what-is-spec-driven-development)
- [⚡ Getting Started](#-getting-started)
  - [Guided Workflow (`/pandawa.ultimate`)](#2-run-guided-workflow-recommended)
  - [Step-by-Step Commands](#3-alternative-step-by-step-commands)
- [🤖 Supported AI Agents](#-supported-ai-agents)
- [🔧 Pandawa CLI Reference](#-pandawa-cli-reference)
  - [Domain Profiles](#domain-profiles)
  - [`pandawa usage`](#pandawa-usage)
  - [`pandawa version`](#pandawa-version)
  - [`pandawa governance`](#pandawa-governance)
  - [`pandawa skill`](#pandawa-skill)
  - [`pandawa run`](#pandawa-run)
- [📚 Core Philosophy](#-core-philosophy)
- [🌟 Development Phases](#-development-phases)
- [🎯 Experimental Goals](#-experimental-goals)
- [🔧 Prerequisites](#-prerequisites)
- [📖 Learn More](#-learn-more)
- [🔍 Troubleshooting](#-troubleshooting)
- [💬 Support](#-support)
- [📄 License](#-license)

## 🤔 What is Spec-Driven Development?

Spec-Driven Development **flips the usual order** of software development. For decades, code was king — specs were just scaffolding built and discarded once the "real work" of writing code began. Spec-Driven Development changes that: **specs become executable**, directly generating working implementations rather than just guiding them.

## ⚡ Getting Started

### 1. Install Pandawa CLI

Choose your preferred installation method:

#### Option 1: Persistent Installation (Recommended)

Install once, use anywhere:

```bash
uv tool install pandawa-cli --from git+https://github.com/zasbita/pandawa.git
```

Then use the tool directly:

```bash
# Create a new project
pandawa init <PROJECT_NAME>

# Or initialize in an existing project
pandawa init . --ai claude
# or
pandawa init --here --ai claude

# Check installed tools
pandawa check
```

To upgrade Pandawa, see the [Upgrade Guide](./docs/upgrade.md) for full instructions. Quick upgrade:

```bash
uv tool install pandawa-cli --force --from git+https://github.com/zasbita/pandawa.git
```

#### Option 2: One-off Usage

Run directly without installation:

```bash
uvx --from git+https://github.com/zasbita/pandawa.git pandawa init <PROJECT_NAME>
```

**Benefits of persistent installation:**

- Tool stays installed and available in PATH
- No shell alias needed
- Better tool management with `uv tool list`, `uv tool upgrade`, `uv tool uninstall`
- Cleaner shell configuration

### 2. Run guided workflow (recommended)

Run your AI assistant in the project directory. The `/pandawa.*` commands will be available.

The fastest way from idea to implementation is **`/pandawa.ultimate`**. This command orchestrates the full lifecycle — from establishing project principles to executing implementation — with confirmation gates between each phase:

```bash
/pandawa.ultimate Build an app that helps me organize my photos into separate albums
```

This command will:

1. Check (or create) your project constitution
2. Create a feature spec from your description
3. Optional: clarify ambiguous requirements
4. Generate a technical plan
5. Break the plan into executable tasks
6. Optional: run a consistency analysis
7. Implement the feature

You stay in control — after each phase you can choose **continue**, **skip** (for optional phases), or **stop**.

> [!TIP]
> If you prefer to run each phase manually or need more control at each step, you can use the individual commands below.

### 3. (Alternative) Step-by-step commands

If you prefer to run each phase one by one:

#### Establish project principles

Use **`/pandawa.constitution`** to create your project's governing principles and development guidelines that will guide all subsequent development.

```bash
/pandawa.constitution Create principles focused on code quality, testing standards, UX consistency, and performance requirements
```

#### Create spec

Use **`/pandawa.specify`** to describe what you want to build. Focus on **what** and **why**, not tech stack.

```bash
/pandawa.specify Build an app that helps me organize my photos into separate albums. Albums are grouped by date and can be reorganized with drag-and-drop on the main page. Albums never nest inside other albums. Inside each album, photos are previewed in a tile-like view.
```

#### Create technical implementation plan

Use **`/pandawa.plan`** to provide your tech stack and architectural choices.

```bash
/pandawa.plan This app uses Vite with as few libraries as possible. Use plain HTML, CSS, and JavaScript where possible. Images are not uploaded anywhere and metadata is stored in a local SQLite database.
```

#### Break into tasks

Use **`/pandawa.tasks`** to generate an actionable task list from your implementation plan.

```bash
/pandawa.tasks
```

#### Execute implementation

Use **`/pandawa.implement`** to execute all tasks and build your feature per plan.

```bash
/pandawa.implement
```

For more detailed step-by-step instructions, see our [full guide](./spec-driven.md).

## 🤖 Supported AI Agents

| Agent                                                                                  | Support | Notes                                                                                                                                     |
| -------------------------------------------------------------------------------------- | ------- | ----------------------------------------------------------------------------------------------------------------------------------------- |
| [Qoder CLI](https://qoder.com/cli)                                                   | ✅      |                                                                                                                                           |
| [Amazon Q Developer CLI](https://aws.amazon.com/developer/learning/q-developer-cli/) | ⚠️      | Amazon Q Developer CLI [does not support](https://github.com/aws/amazon-q-developer-cli/issues/3064) custom arguments for slash commands. |
| [Amp](https://ampcode.com/)                                                          | ✅      |                                                                                                                                           |
| [Auggie CLI](https://docs.augmentcode.com/cli/overview)                              | ✅      |                                                                                                                                           |
| [Claude Code](https://www.anthropic.com/claude-code)                                 | ✅      |                                                                                                                                           |
| [CodeBuddy CLI](https://www.codebuddy.ai/cli)                                        | ✅      |                                                                                                                                           |
| [Codex CLI](https://github.com/openai/codex)                                         | ✅      |                                                                                                                                           |
| [Cursor](https://cursor.sh/)                                                         | ✅      |                                                                                                                                           |
| [Gemini CLI](https://github.com/google-gemini/gemini-cli)                            | ✅      |                                                                                                                                           |
| [GitHub Copilot](https://code.visualstudio.com/)                                     | ✅      |                                                                                                                                           |
| [IBM Bob](https://www.ibm.com/products/bob)                                          | ✅      | IDE-based agent with slash command support                                                                                          |
| [Kilo Code](https://github.com/Kilo-Org/kilocode)                                    | ✅      |                                                                                                                                           |
| [opencode](https://opencode.ai/)                                                     | ✅      |                                                                                                                                           |
| [Qwen Code](https://github.com/QwenLM/qwen-code)                                     | ✅      |                                                                                                                                           |
| [Roo Code](https://roocode.com/)                                                     | ✅      |                                                                                                                                           |
| [SHAI (OVHcloud)](https://github.com/ovh/shai)                                       | ✅      |                                                                                                                                           |
| [Windsurf](https://windsurf.com/)                                                    | ✅      |                                                                                                                                           |

## 🔧 Pandawa CLI Reference

The `pandawa` command supports the following options:

### Commands

| Command      | Description                                                                                                                                             |
| ------------ | ------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `init`       | Initialize a new Pandawa project from the latest template                                                                                                 |
| `profile`    | Manage domain knowledge profiles — list, check update (`status`), pull update (`update`), pin local path                                          |
| `check`      | Check `git` plus every supported [AI agent](#-supported-ai-agents) CLI/IDE tool installed on your machine                                          |
| `version`    | Show CLI version, platform info, and latest template release                                                                                         |
| `usage`      | Show Claude Code token usage and cost estimate for the current project                                                                                 |
| `governance` | Manage governance plugins (list, install, uninstall, activate, disable)                                                                                 |
| `skill`      | Manage skill plugins (list, install, uninstall, enable, disable)                                                                                        |
| `run`        | Run `/pandawa.*` skills via Claude Code from the terminal                                                                                                 |

Each command prints a small **Process Audit** panel when finished (duration, and for AI-based commands, token usage/cost estimate) and appends a JSON-lines record to `.pandawa/audit.log` in the project (or `~/.config/pandawa/audit.log` when run outside a project). This is purely an informative local log for your own records — nothing is sent anywhere. `pandawa usage` reads the same session data to summarize costs across sessions or commands.

### Domain Profiles

Profiles are **domain knowledge overlays** that teach your AI agent standards, patterns, and architectural decisions for a specific domain — without changing your base template.

> [!NOTE]
> Profiles are applied via `pandawa init`, not via a separate `pandawa profile install` command — `pandawa profile` has `list`, `refresh`, `set-local`, `status`, and `update` (see below).

Apply a profile when you initialize a new project:

```bash
pandawa init my-project --ai claude --profile tmforum-oda
```

Or when running `pandawa init` interactively (without `--profile`), you will be prompted to choose from an arrow-key menu.

To add a profile to an already-initialized project, re-run `init` in place:

```bash
pandawa init --here --force --ai claude --profile tmforum-oda
```

Profile folders are fetched live from git (`main`, no CLI release needed) and extracted to `.pandawa/profiles/<profile-id>/`. Your AI agent's instruction file is automatically updated to load its constitution and follow its standards.

#### Available Profiles

| Profile ID | Name | Description |
| --- | --- | --- |
| `tmforum-oda` | TM Forum ODA Constitution | Reusable TM Forum Open Digital Architecture constitution framework: API governance, DDD, CQRS, event-driven patterns for BSS/OSS systems |
| `tmforum-oda-door-v3` | TM Forum ODA Design DOOR v3 | Everything in `tmforum-oda`, plus DOOR v3 design system — NestJS, CQRS, React MFE, Module Federation |
| `pegadaian` | Pegadaian Support Service Constitution | NestJS backend + Vue 3 Module Federation frontend constitution for Pegadaian AI team services. **Status: Draft** — see Known Gaps in `constitution/00-index.md` before treating as binding |

Run `pandawa profile list` anytime to see the current set of known profile IDs and names (this table may change as new profiles are added — the CLI list is the source of truth). Run `pandawa profile refresh` to sync the local catalog with `main` — profiles appear here as soon as they merge, without a CLI release.

#### Adding a new profile (self-service)

Profiles live in the **`pandawa-marketplace-tooling`** repo (`https://github.com/zasbita/pandawa-marketplace-tooling.git`), alongside skill/agent plugins as a separate top-level concept — one repo, one contribution flow, one CI validation job for both. Adding a profile is fully self-service — no CLI code change, no CLI release, no packaging step:

1. In your clone of `pandawa-marketplace-tooling`, add a folder at `profiles/<your-profile>/` with a manifest `profile.json` (`{"id", "name", "description"}`) plus your `constitution/`, `architecture/`, `governance/`, `validation/`, `prompts/`, `SKILL.md`, etc. — including whatever frontend stack your profile targets.
2. Add one entry `{"id": "<your-id>", "path": "profiles/<your-profile>"}` to `profiles.json` at the repo root — this is the only shared file you touch, and it uses the same one-line registration pattern as `.claude-plugin/marketplace.json`.
3. Run `python tools/validate-marketplace.py .` there, then open a merge request (see that repo's `CONTRIBUTING.md`/`CODEOWNERS`). Once merged to `main`, `pandawa init --profile <your-id>` works for everyone — `pandawa` fetches your profile folder live via the repository-archive API, with no zip/release/CI step in this repo.

Before merging, test locally against your clone with `pandawa init --profile <your-id> --profile-path <path-to-your-clone>/profiles/<your-profile>` (bypasses the catalog check entirely since the source is explicit).

> [!TIP]
> For a full end-to-end collaboration guide (plugin vs profile decision, complete domain-profile folder anatomy, CODEOWNERS, breaking-change rules), see [`pandawa-marketplace-tooling/docs/COLLABORATION-GUIDE.md`](https://github.com/zasbita/pandawa-marketplace-tooling/blob/main/docs/COLLABORATION-GUIDE.md), or this repo's [Marketplace docs](docs/marketplace.md).

#### What gets installed by a profile

```text
.pandawa/
└── profiles/
    └── tmforum-oda/
        ├── SKILL.md                  ← Sub-agent definition (Claude)
        ├── constitution/             ← 16 engineering law files (MUST/SHOULD/MUST NOT)
        ├── architecture/             ← ODA Canvas patterns, reference tables
        ├── governance/               ← Repository & PR governance rules
        ├── prompts/                  ← Ready-to-use agent prompts for backend/frontend generation
        ├── templates/                ← Module scaffolding templates
        ├── validation/               ← Rule book for API, backend, frontend
        └── recommendations/          ← Gap analysis & migration roadmap templates
```

Your AI agent's instruction file (`CLAUDE.md`, `GEMINI.md`, etc.) is updated to always load the profile constitution in every session. For Claude, a sub-agent `.claude/agents/<profile-id>.md` is also installed for on-demand use.

> [!NOTE]
> A profile's `governance/` folder is unrelated to the [`pandawa governance`](#pandawa-governance) command below — same word, different concept. A profile's `governance/` is static reference docs (repo/PR rules) copied for the agent to read; it is never registered in the governance guard and has no runtime enforcement. `pandawa governance` is a different, mutually exclusive Claude Code plugin system with real `PreToolUse` hook guards that can block tool use. Installing a profile does not install or activate any governance plugin.

### `pandawa profile` — list, check update, & pin local profile

| Subcommand | Description |
| ---------- | ----------- |
| `list` | List all known profile IDs/names/versions (with best-effort refresh first), plus local path if any pinned via `set-local` |
| `refresh` | Sync local profile catalog from `profiles.json` in `pandawa-marketplace-tooling` on `main`, independent of any CLI release |
| `status` | Inside a project: compare installed profile version (`.pandawa/profile-lock.json`) with the latest in the catalog, flagging which is "update available" |
| `update <key>` | Inside a project: re-fetch profile `<key>` content from `main` (or `--profile-path` local), overwrite `.pandawa/profiles/<key>/`, and update lockfile |
| `set-local <key> <path>` | Pin a local directory as a profile source so `pandawa init --profile <key>` uses it instead of downloading from Git (useful when authoring/testing a profile) |

```bash
# See available profiles (with their latest versions)
pandawa profile list

# Inside a project with installed profiles: check for updates
pandawa profile status

# Pull that update
pandawa profile update tmforum-oda

# Point a profile to a local directory instead of downloading
pandawa profile set-local tmforum-oda-door-v3 ../pandawa-marketplace-tooling/profiles/tmforum-oda-door-v3
```

> [!NOTE]
> `version` in `profile.json` is **not** a pin mechanism — `pandawa init --profile` and
> `pandawa profile update` always fetch the current `main`. This version is purely for
> visibility: `pandawa` records the installed version in `.pandawa/profile-lock.json`
> per project, and `pandawa profile status` compares it with the catalog so
> updates merged to `pandawa-marketplace-tooling` are actually **visible**,
> not silently changed on `main`.

### `pandawa init` Arguments & Options

| Argument/Option | Type | Description |
| --------------- | ---- | ----------- |
| `<project-name>` | Argument | Name for your new project's directory (optional if using `--here`, or use `.` for current directory) |
| `--ai` | Option | AI assistant to use: `claude`, `gemini`, `copilot`, `cursor-agent`, `qwen`, `opencode`, `codex`, `windsurf`, `kilocode`, `auggie`, `roo`, `codebuddy`, `amp`, `shai`, `q`, `bob`, or `qoder` |
| `--script` | Option | Script variant to use: `sh` (bash/zsh) or `ps` (PowerShell) |
| `--ignore-agent-tools` | Flag | Skip AI agent tool checks like Claude Code |
| `--no-git` | Flag | Skip git repository initialization |
| `--here` | Flag | Initialize project in current directory instead of creating a new one |
| `--force` | Flag | Force merge/overwrite when using `--here` (skip confirmation) — also how you re-apply `init` (e.g., to add `--profile`) to an already-initialized project |
| `--skip-tls` | Flag | Skip SSL/TLS verification (not recommended) |
| `--debug` | Flag | Show verbose diagnostic output for network and extraction failures |
| `--gitlab-token` | Option | GitLab token for API requests (or set env `GL_TOKEN`) — also used as fallback for private GitLab instances; public GitHub install needs no token |
| `--profile` | Option | Domain profile to apply (e.g., `tmforum-oda`) — see [Domain Profiles](#domain-profiles) |
| `--profile-path` | Option | Use a local directory as profile source instead of downloading (development/testing) |
| `--no-marketplace` | Flag | Skip Pandawa plugin marketplace registration in project (Claude only) |
| `--marketplace-url` | Option | Override Pandawa marketplace git URL (or set `PANDAWA_MARKETPLACE_URL`) |
| `--no-guardrails` | Flag | Skip writing baseline deny-first permission guardrails to `.claude/settings.json` (Claude only) |
| `--no-claude-md` | Flag | Skip scaffolding starter `CLAUDE.md` project context file |

### Examples

```bash
# Initialize a basic project
pandawa init my-project

# Initialize with a specific AI assistant
pandawa init my-project --ai claude
pandawa init my-project --ai cursor-agent
pandawa init my-project --ai qoder
pandawa init my-project --ai windsurf
pandawa init my-project --ai amp
pandawa init my-project --ai shai
pandawa init my-project --ai bob

# Initialize with PowerShell scripts (Windows/cross-platform)
pandawa init my-project --ai copilot --script ps

# Initialize in current directory
pandawa init . --ai copilot
# or use --here flag
pandawa init --here --ai copilot

# Force merge into a non-empty current directory without confirmation
pandawa init . --force --ai copilot
# or
pandawa init --here --force --ai copilot

# Skip git initialization
pandawa init my-project --ai gemini --no-git

# Enable debug output for troubleshooting
pandawa init my-project --ai claude --debug

# Check system requirements
pandawa check

# Initialize with TM Forum ODA domain profile
pandawa init my-project --ai claude --profile tmforum-oda

# Add a profile to an existing project in the current directory
pandawa init --here --force --ai claude --profile tmforum-oda
```

![Pandawa CLI bootstrapping a new project](./media/pandawa_cli.gif)

---

### `pandawa usage`

Show Claude Code token usage and cost estimate for the current project. Reads session history from `~/.claude/projects/` and aggregates input/output/cache tokens, turn counts, model, and cost per session.

```bash
# Show last 10 sessions (default)
pandawa usage

# Show all sessions
pandawa usage --limit 0

# Show per-command breakdown with cost and duration
pandawa usage --commands

# Show AI-DLC style delivery metrics (predictability, cycle time, phase mix)
pandawa usage --delivery

# Show usage for a specific project directory
pandawa usage --cwd /path/to/my-project
```

| Option | Description |
| ------ | ----------- |
| `--limit`, `-n` | Number of recent sessions to show (default: `10`, `0` = all) |
| `--cwd` | Project directory to read sessions from (default: current directory) |
| `--commands`, `-c` | Show per-command `/pandawa.*` breakdown with cost and duration |
| `--delivery`, `-d` | Show AI-DLC style delivery metrics: **predictability rate** (tasks completed vs planned in `tasks.md`, target >80%), **cycle time** end-to-end, and **phase mix** per command. Metrics that need an A/B baseline (velocity vs non-AI, defect rate normalized) are intentionally not fabricated — reported honestly as needing a comparator |

---

### `pandawa version`

Show CLI version, platform info, and latest template release from the registry.

```bash
pandawa version
```

| Option | Description |
| ------ | ----------- |
| `--gitlab-token` | GitLab token (or set env `GL_TOKEN` / `GITLAB_TOKEN`) — optional, GitHub public releases need no token |

---

### `pandawa governance`

Manage **governance plugins** — plugins that enforce project-wide rules and constitution. Only one governance plugin may be active at a time.

> [!NOTE]
> Not to be confused with a profile's `governance/` folder (see [What gets installed by a profile](#what-gets-installed-by-a-profile)) — that is static reference content bundled with a domain profile, with no runtime enforcement. This command manages a different, mutually exclusive type: installable Claude Code plugins with real `PreToolUse` guard hooks that can block tool use if the one-active invariant is violated.

```bash
# List locally installed governance plugins
pandawa governance list

# List all available governance plugins (installed + marketplace)
pandawa governance list marketplace

# Sync catalog from marketplace
pandawa governance refresh

# Download a governance plugin to local store
pandawa governance install tmf-oda-constitution

# Activate a governance plugin
pandawa governance use tmf-oda-constitution

# Show which governance plugin is currently active
pandawa governance status

# Deactivate the active governance plugin
pandawa governance disable

# Remove a governance plugin from local store
pandawa governance uninstall tmf-oda-constitution
```

| Subcommand | Description |
| ---------- | ----------- |
| `list [marketplace]` | List locally installed governance plugins; add `marketplace` to include all available |
| `refresh` | Sync governance catalog from marketplace |
| `install <name>` | Download governance plugin to local store (without activating) |
| `uninstall <name>` | Remove governance plugin from local store |
| `use <name>` | Activate a governance plugin (deactivating any previously active) |
| `status` | Show the currently active governance plugin |
| `disable [name]` | Deactivate the active governance plugin (or the named one) |

---

### `pandawa skill`

Manage **skill plugins** — on-demand capabilities that extend what your AI agent can do. Multiple skills can be active at once.

```bash
# List locally installed skills
pandawa skill list

# List all available skills (installed + marketplace)
pandawa skill list marketplace

# Download and activate a skill
pandawa skill install neuron-plan

# Activate an already-installed skill
pandawa skill enable neuron-plan

# Deactivate a skill (keep installed)
pandawa skill disable neuron-plan

# Remove a skill from local store
pandawa skill uninstall neuron-plan
```

| Subcommand | Description |
| ---------- | ----------- |
| `list [marketplace]` | List locally installed skills; add `marketplace` to include all available |
| `install <name>` | Download skill plugin and activate immediately |
| `uninstall <name>` | Remove skill plugin from local store |
| `enable <name>` | Activate an already-installed skill plugin |
| `disable <name>` | Deactivate a skill plugin without removing it |

---

### `pandawa run`

Run `/pandawa.*` skills directly via Claude Code from the terminal — useful for scripting or CI.

```bash
pandawa run constitution "Create REST API for a todo app"
pandawa run brd "focus on billing module"
pandawa run specify "user authentication with OAuth2"
pandawa run plan
pandawa run clarify
pandawa run tasks
pandawa run implement
pandawa run analyze
pandawa run checklist
pandawa run test src/
pandawa run redesign "form create Projected Cost, follow new design file"
pandawa run deploy "prepare staging pipeline"
pandawa run operate "wire observability for billing service"
pandawa run postmortem "latency spike incident on orders endpoint"
```

| Subcommand | Description |
| ---------- | ----------- |
| `constitution [goal]` | Run `/pandawa.constitution` — create or update project governing principles |
| `brd [scope]` | Run `/pandawa.brd` — reverse-engineer BRD from existing codebase |
| `specify [goal]` | Run `/pandawa.specify` — define requirements and user stories |
| `plan [goal]` | Run `/pandawa.plan` — create technical implementation plan |
| `tasks [goal]` | Run `/pandawa.tasks` — generate actionable task list |
| `implement [goal]` | Run `/pandawa.implement` — execute tasks to build feature |
| `clarify [goal]` | Run `/pandawa.clarify` — clarify underspecified requirements |
| `analyze [goal]` | Run `/pandawa.analyze` — cross-artifact consistency & coverage analysis |
| `checklist [goal]` | Run `/pandawa.checklist` — generate custom quality checklist |
| `test [path]` | Run `/pandawa.test` — generate tests, run code quality checks, and report bugs |
| `redesign [target]` | Run `/pandawa.redesign` — incrementally rework a part of an already-implemented feature |
| `deploy [scope]` | Run `/pandawa.deploy` — prepare deployment automation (containerization, CI/CD, config) |
| `operate [mode]` | Run `/pandawa.operate` — wire observability, analyze telemetry/anomalies, and resolve incidents |
| `postmortem [incident]` | Run `/pandawa.postmortem` — turn production incidents/learnings into spec & constitution updates |

---

### Available Slash Commands

After running `pandawa init`, your AI coding agent will have access to the following slash commands for structured development:

#### Workflow Command

Run the full SDD lifecycle in a single guided session:

| Command | Description |
| --- | --- |
| `/pandawa.ultimate` | End-to-end orchestrator — runs constitution through implementation with confirmation gates between each phase. Detects existing artifacts and offers to continue from the last checkpoint |

```bash
/pandawa.ultimate Build an app that helps me organize my photos into separate albums
```

This single command takes you through all build phases (constitution, specify, clarify, plan, tasks, analyze, implement), pausing after each for your confirmation before continuing. Optional phases (clarify, analyze) can be skipped at their gates. Operations commands (`/pandawa.deploy`, `/pandawa.operate`, `/pandawa.postmortem`) are not part of this orchestration — run them separately in a later session when you're ready to release.

If you run `/pandawa.ultimate` again in a project that already has some artifacts (e.g., spec exists but plan doesn't), it will scan what exists on disk first and offer to **(A)** start a new feature, **(B)** continue from the phase after the last completed artifact, or **(C)** fully restart the current feature. Stopping at any gate prints an abort summary with the exact manual commands to resume later — nothing is lost if you stop mid-way.

#### Brownfield Command

For brownfield projects (`pandawa init --here` on an existing codebase), run this first so the remaining workflow has real context instead of starting from an empty spec:

| Command | Description |
| --- | --- |
| `/pandawa.brd` | Reverse-engineer Business Requirements Document from existing codebase — becomes background context for `/pandawa.specify` and `/pandawa.constitution` |

```bash
/pandawa.brd
```

#### Core Commands

Essential commands for Spec-Driven Development (also runnable one by one):

| Command               | Description                                                              |
| --------------------- | ------------------------------------------------------------------------ |
| `/pandawa.constitution` | Create or update project governing principles and development guidelines |
| `/pandawa.specify`      | Define what you want to build (requirements and user stories)            |
| `/pandawa.plan`         | Create technical implementation plan with your chosen tech stack        |
| `/pandawa.tasks`        | Generate actionable task list for implementation             |
| `/pandawa.implement`    | Execute all tasks to build the feature per plan             |

#### Optional Commands

Additional commands for better quality and validation:

| Command            | Description                                                                                                                          |
| ------------------ | ------------------------------------------------------------------------------------------------------------------------------------ |
| `/pandawa.clarify`   | Clarify underspecified areas (recommended before `/pandawa.plan`; formerly `/quizme`)                                                  |
| `/pandawa.analyze`   | Cross-artifact consistency & coverage analysis (run after `/pandawa.tasks`, before `/pandawa.implement`)                                 |
| `/pandawa.checklist` | Generate custom quality checklist that validates completeness, clarity, and consistency of requirements (e.g., "unit test for Bahasa Indonesia") |
| `/pandawa.test`      | Generate missing unit tests, run SonarQube-style code quality checks (code smell, duplication, complexity, security), and detect functional bugs — proving each bug with a failing test and reporting a Bug Report when found |
| `/pandawa.redesign`  | Incrementally rework a part of an already-implemented feature (form, page, endpoint, or table) — scoped edit with checkpoint & rollback, instead of regenerating from scratch |
| `/pandawa.taskstoissues` | Create GitHub issues from `tasks.md` via GitHub MCP server. Only runs if `git remote` is a GitHub URL — skips for GitLab-hosted projects |

#### Operations Commands (post-implementation)

After a feature is implemented, these commands carry the lifecycle toward release and operations — usually run in a separate session when you're ready to ship:

| Command | Description |
| ------- | ----------- |
| `/pandawa.deploy` | Prepare deployment automation — containerization, CI/CD pipeline, and environment config — following Plan-Verify-Generate. Never performs a live deploy without explicit confirmation; by default stops at validated artifacts + dry-run |
| `/pandawa.operate` | Wire observability (logs/metrics/traces/health), analyze telemetry to detect anomalies, and help investigate + resolve production incidents (using `/pandawa.redesign`'s scoped-edit discipline) |
| `/pandawa.postmortem` | Close the SDD feedback loop — turn production incidents/telemetry/learnings into spec, NFR, and constitution updates so fixes survive the next regeneration. Does not touch application code |

### Environment Variables

| Variable | Description |
| -------- | ----------- |
| `PANDAWA_FEATURE` | Override feature detection for non-Git repos. Set to a feature directory name (e.g., `001-photo-albums`) to work on a specific feature when not using Git branches.<br/>**Must be set in your agent's context before using `/pandawa.plan` or later commands.** |

## 📚 Core Philosophy

Spec-Driven Development is a structured process that emphasizes:

- **Intent-based development** where specs define "*what*" before "*how*"
- **Rich spec creation** using guardrails and organizational principles
- **Multi-step refinement** instead of one-shot code generation from prompt
- **Heavy reliance** on advanced AI model capabilities for spec interpretation

## 🌟 Development Phases

| Phase                                    | Focus                    | Main Activities                                                                                                                                                     |
| ---------------------------------------- | ------------------------ | ------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| **Greenfield Development** ("Greenfield")    | Generate from scratch    | <ul><li>Start from high-level requirements</li><li>Generate specifications</li><li>Plan implementation steps</li><li>Build production-ready app</li></ul> |
| **Creative Exploration**                 | Parallel implementation | <ul><li>Explore diverse solutions</li><li>Support various tech stacks & architectures</li><li>Experiment with UX patterns</li></ul>                         |
| **Iterative Enhancement** ("Brownfield") | Brownfield modernization | <ul><li>Add features iteratively</li><li>Modernize legacy systems</li><li>Adapt processes</li></ul>                                                                |

## 🎯 Experimental Goals

Our research and experiments focus on:

### Technology independence

- Build apps using diverse tech stacks
- Validate the hypothesis that Spec-Driven Development is a process, not tied to a specific technology, programming language, or framework

### Enterprise constraints

- Demonstrate mission-critical application development
- Incorporate organizational constraints (cloud provider, tech stack, engineering practices)
- Support enterprise design systems and compliance requirements

### User-centric development

- Build apps for different user cohorts and preferences
- Support various development approaches (from vibe-coding to AI-native development)

### Creative & iterative process

- Validate the concept of parallel implementation exploration
- Provide a robust iterative feature development workflow
- Extend the process to handle upgrades and modernization

## 🔧 Prerequisites

- **Linux/macOS/Windows**
- A [supported AI coding agent](#-supported-ai-agents).
- [uv](https://docs.astral.sh/uv/) for package management
- [Python 3.11+](https://www.python.org/downloads/)
- [Git](https://git-scm.com/downloads)

If you encounter an issue with an agent, please open an issue so we can fix the integration.

## 📖 Learn More

- **[Complete Spec-Driven Development Methodology](./spec-driven.md)** - In-depth process deep dive
- **[Detailed Walkthrough](#-detailed-process)** - Step-by-step implementation guide

---

## 📋 Detailed Process

<details>
<summary>Click to expand detailed step-by-step walkthrough</summary>

You can use the Pandawa CLI to bootstrap your project, which will bring the required artifacts into your environment. Run:

```bash
pandawa init <project_name>
```

Or initialize in the current directory:

```bash
pandawa init .
# or use --here flag
pandawa init --here
# Skip confirmation when directory already has files
pandawa init . --force
# or
pandawa init --here --force
```

![Pandawa CLI bootstrapping a new project](./media/pandawa_cli.gif)

You will be prompted to choose your AI assistant. You can also specify it directly:

```bash
pandawa init <project_name> --ai claude
pandawa init <project_name> --ai gemini
pandawa init <project_name> --ai copilot

# Or in the current directory:
pandawa init . --ai claude
pandawa init . --ai codex

# or use --here flag
pandawa init --here --ai claude
pandawa init --here --ai codex

# Force merge into a non-empty current directory
pandawa init . --force --ai claude

# or
pandawa init --here --force --ai claude
```

The CLI will check whether you have Claude Code, Gemini CLI, Cursor CLI, Qwen CLI, opencode, Codex CLI, Qoder CLI, or Amazon Q Developer CLI installed. If not, or if you prefer to get the template without strict tool checks, use `--ignore-agent-tools` with your command:

```bash
pandawa init <project_name> --ai claude --ignore-agent-tools
```

### **STEP 1:** Establish project principles

Open the project folder and run your AI agent. In our example we use `claude`.

You will know everything is configured correctly if you see the `/pandawa.constitution`, `/pandawa.specify`, `/pandawa.plan`, `/pandawa.tasks`, and `/pandawa.implement` commands available.

The first step should be to establish your project's governing principles using `/pandawa.constitution`. This helps ensure consistent decision-making across all subsequent phases:

```text
/pandawa.constitution Create principles focused on code quality, testing standards, UX consistency, and performance requirements. Include governance on how these principles should guide technical decisions and implementation choices.
```

This step creates or updates the file `.pandawa/memory/constitution.md` with your project's fundamental guidelines that the AI agent will reference during spec, planning, and implementation.

### **STEP 2:** Create project spec

After project principles are set, you can now create a functional spec. Use `/pandawa.specify` then provide concrete requirements for the project you want to build.

> [!IMPORTANT]
> Describe in as much detail as possible *what* you are trying to build and *why*. **Don't focus on tech stack at this stage**.

Example prompt:

```text
Develop Taskify, a team productivity platform. This app should allow users to create projects, add team
members, assign tasks, comment and move tasks across boards in a Kanban style. For the initial phase of this feature,
we call it "Create Taskify", we will have many users but users will be declared upfront, pre-defined.
I want five users in two different categories, one product manager and four engineers. Create three different sample
projects. We use standard Kanban columns for each task's status, such as "To Do,"
"In Progress," "In Review," and "Done." There will be no login for this app as it is an early test
to make sure our basic features are ready. For each task in the UI, on the task card,
you should be able to change the task's current status across columns on the Kanban board. You should be able
to leave unlimited comments for a given card. You should be able, from that task card
itself, to assign any valid user. When you first open Taskify, a list of five users to choose from will appear.
No password is required. When you click a user, you enter the main view, which shows the list of
projects. When you click a project, you open the Kanban board for that project. You will see its columns.
You can drag-and-drop cards back and forth between different columns. You will see any card that
is assigned to you, the currently logged-in user, in a different color from the others, so you can quickly
see yours. You can edit your own comments but not others'. You can
delete your own comments but not others'.
```

After submitting this prompt, you will see Claude Code start the planning and spec drafting process. It will also trigger several built-in scripts to prepare the repository.

After this step completes, you should have a new branch (e.g., `001-create-taskify`), plus a new spec in `specs/001-create-taskify`.

The generated spec should contain a set of user stories and functional requirements as defined in the template.

At this stage, your project folder should look roughly like:

```text
└── .pandawa
    ├── memory
    │  └── constitution.md
    ├── scripts
    │  ├── check-prerequisites.sh
    │  ├── common.sh
    │  ├── create-new-feature.sh
    │  ├── setup-plan.sh
    │  └── update-claude-md.sh
    ├── specs
    │  └── 001-create-taskify
    │      └── spec.md
    └── templates
        ├── plan-template.md
        ├── spec-template.md
        └── tasks-template.md
```

### **STEP 3:** Clarify functional spec (required before planning)

With the base spec in place, you can now clarify any requirements that weren't captured correctly on the first try.

You should run a structured clarification workflow **before** creating the technical plan to reduce rework later.

Recommended order:

1. Use `/pandawa.clarify` (structured) — sequential coverage-based questions that record answers in the Clarifications section.
2. Optional: follow up with free-form ad-hoc refinement if anything still feels unclear.

If you intentionally want to skip clarification (e.g., spike or exploratory prototype), say so explicitly so the agent doesn't block on missing clarification.

Example free-form refinement prompt (after `/pandawa.clarify` if still needed):

```text
For each sample project or project you create there should be a variable number of tasks between 5 and 15
tasks for each, distributed randomly across various completion states. Make sure there is
at least one task in every completion stage.
```

You should also ask Claude Code to validate the **Review & Acceptance Checklist**, checking items that are validated / meet requirements and leaving the rest unchecked. You can use this prompt:

```text
Read the review and acceptance checklist and check each item if the feature spec meets its criteria. Leave empty otherwise.
```

It's important to use the interaction with Claude Code as an opportunity to clarify and ask questions about the spec — **don't treat its first attempt as final**.

### **STEP 4:** Generate plan

You can now be specific about tech stack and other technical requirements. You can use the `/pandawa.plan` built into the project template with a prompt like:

```text
We will generate this using .NET Aspire, with Postgres as database. The frontend should use
Blazor server with drag-and-drop task board, real-time updates. There should be REST APIs built with projects APIs,
tasks APIs, and notifications APIs.
```

The output of this step will include a number of detailed implementation documents, with your directory structure looking roughly like:

```text
.
├── CLAUDE.md
├── memory
│  └── constitution.md
├── scripts
│  ├── check-prerequisites.sh
│  ├── common.sh
│  ├── create-new-feature.sh
│  ├── setup-plan.sh
│  └── update-claude-md.sh
├── specs
│  └── 001-create-taskify
│      ├── contracts
│      │  ├── api-spec.json
│      │  └── signalr-spec.md
│      ├── data-model.md
│      ├── plan.md
│      ├── quickstart.md
│      ├── research.md
│      └── spec.md
└── templates
    ├── CLAUDE-template.md
    ├── plan-template.md
    ├── spec-template.md
    └── tasks-template.md
```

Check the `research.md` to ensure the correct tech stack is used per your instructions. You can ask Claude Code to fix it if something looks off, or even ask it to check locally installed platform/framework versions you require (e.g., .NET).

Additionally, you may want to ask Claude Code to research details about the chosen tech stack if it is fast-moving (e.g., .NET Aspire, JS frameworks) with a prompt like:

```text
I want you to look through the implementation plan and implementation details, looking for areas that could
benefit from additional research because .NET Aspire is a fast-changing library. For any areas you identify
as needing additional research, I want you to update the research document with additional details about the specific versions
we will use in this Taskify app and run parallel research tasks to clarify
any details using web research.
```

During this process you may find Claude Code getting stuck researching the wrong thing — you can steer it with a prompt like:

```text
I think we need to break this into a series of steps. First, identify the list of tasks
you will need during implementation that you are not yet sure about or would benefit
from additional research. Write down that list of tasks. Then for each of these tasks,
I want you to run a separate research task so the end result is we
research all those specific tasks in parallel. What I see you doing seems like you are
researching .NET Aspire generally and I'm not sure that will be very useful for us in this case.
That research is too unfocused. The research needs to help you answer specific targeted questions.
```

> [!NOTE]
> Claude Code may be overly eager and add components you didn't ask for. Ask it to clarify the rationale and source of those changes.

### **STEP 5:** Validate the plan

With the plan in place, you should ask Claude Code to walk through it to ensure nothing is missed. You can use a prompt like:

```text
Review the plan for any missing or underspecified areas. Flag any assumptions that need confirmation before we proceed to tasks.
```

### **STEP 6:** Generate tasks

Use `/pandawa.tasks` to break the plan into small, testable tasks:

```bash
/pandawa.tasks
```

This will create `tasks.md` with tasks grouped by user story, each referencing the relevant `FR-###` requirement.

### **STEP 7:** Implement

Run `/pandawa.implement` to execute the tasks. The agent will work through the task list, updating `tasks.md` as it completes each item and running verification (`verify_command`) before marking a task done.

### **STEP 8:** Verify & Ship

Run `/pandawa.analyze` (before implement) for cross-artifact consistency, `/pandawa.test` for test generation + SonarQube-style quality checks, and `/pandawa.deploy` / `/pandawa.operate` when ready to ship.

</details>

---

## 🔍 Troubleshooting

See [Troubleshooting Guide](./docs/troubleshooting.md) or open an issue.

## 💬 Support

For support, please check our [Support Guide](./SUPPORT.md) or open an issue on GitHub. For Neuron internal use, the canonical source remains [git.neuron.id/research/pandawa](https://git.neuron.id/research/pandawa).

## 📄 License

This project is licensed under the terms of the MIT open source license. Please see the [LICENSE](./LICENSE) file for full terms.

