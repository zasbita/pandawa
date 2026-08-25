<div align="center">
    <img src="/media/logo_large.png" alt="Pandawa Logo" width="200" height="200"/>
</div>

# Quick Start Guide

This guide will help you get started with Spec-Driven Development using Pandawa.

> [!NOTE]
> All automation scripts now provide both Bash (`.sh`) and PowerShell (`.ps1`) variants. The `pandawa` CLI auto-selects based on OS unless you pass `--script sh|ps`.

## The 6-Step Process

> [!TIP]
> **Context Awareness**: Pandawa commands automatically detect the active feature based on your current Git branch (e.g., `001-feature-name`). To switch between different specifications, simply switch Git branches.

<!-- -->

> [!TIP]
> **One entry point (any agent)**: not sure which command to use? Run `/pandawa` with no arguments for a guided menu, or describe your goal and it routes you to the right command. It works the same on every supported agent, never bypasses a target's gates, and never auto-runs a governed flow without confirming. Capabilities beyond SDD (e.g. governed delivery, documents) live in the pandawa marketplace and are installed on demand.

### Step 1: Install Pandawa

**In your terminal**, run the `pandawa` CLI command to initialize your project:

```bash
# Create a new project directory
uvx --from git+https://git.neuron.id/research/pandawa.git pandawa init <PROJECT_NAME>

# OR initialize in the current directory
uvx --from git+https://git.neuron.id/research/pandawa.git pandawa init .
```

Pick script type explicitly (optional):

```bash
uvx --from git+https://git.neuron.id/research/pandawa.git pandawa init <PROJECT_NAME> --script ps  # Force PowerShell
uvx --from git+https://git.neuron.id/research/pandawa.git pandawa init <PROJECT_NAME> --script sh  # Force POSIX shell
```

> [!TIP]
> **Working with an existing codebase?** Before Step 2, run `/pandawa.brd` in the chat. It reverse-engineers a compact per-module semantic map from your current code into `docs/brd/` (a system-wide `00-overview.md` plus one terse `modules/<slug>.md` per module — capabilities, entities, API surface, data flow, dependencies, test coverage), so `/pandawa.constitution` and `/pandawa.specify` start from real context instead of a blank slate — at a fraction of a full document's token cost. Skip this step for a brand-new project.

<!-- -->

> [!TIP]
> **Targeting a specific domain (e.g. telecom/TM Forum ODA)?** Pass `--profile <profile-id>` to `pandawa init` (or pick one from the interactive menu) to load domain-specific constitution rules, architecture patterns, and templates alongside the base Pandawa template. See the [Domain Profiles reference](https://git.neuron.id/research/pandawa/blob/main/README.md#domain-profiles) in the main README.

<!-- -->

> [!TIP]
> **In a hurry?** Instead of running Steps 2–6 one at a time, you can run `/pandawa.ultimate <your goal>` once and it drives the whole lifecycle for you, pausing for your confirmation between each phase. See [Guided Workflow](https://git.neuron.id/research/pandawa/blob/main/README.md#2-run-the-guided-workflow-recommended) in the main README.

### Step 2: Define Your Constitution

**In your AI Agent's chat interface**, use the `/pandawa.constitution` slash command to establish the core rules and principles for your project. You should provide your project's specific principles as arguments.

```markdown
/pandawa.constitution This project follows a "Library-First" approach. All features must be implemented as standalone libraries first. We use TDD strictly. We prefer functional programming patterns.
```

### Step 3: Create the Spec

**In the chat**, use the `/pandawa.specify` slash command to describe what you want to build. Focus on the **what** and **why**, not the tech stack.

```markdown
/pandawa.specify Build an application that can help me organize my photos in separate photo albums. Albums are grouped by date and can be re-organized by dragging and dropping on the main page. Albums are never in other nested albums. Within each album, photos are previewed in a tile-like interface.
```

### Step 4: Refine the Spec

**In the chat**, use the `/pandawa.clarify` slash command to identify and resolve ambiguities in your specification. You can provide specific focus areas as arguments.

```bash
/pandawa.clarify Focus on security and performance requirements.
```

### Step 5: Create a Technical Implementation Plan

**In the chat**, use the `/pandawa.plan` slash command to provide your tech stack and architecture choices.

```markdown
/pandawa.plan The application uses Vite with minimal number of libraries. Use vanilla HTML, CSS, and JavaScript as much as possible. Images are not uploaded anywhere and metadata is stored in a local SQLite database.
```

### Step 6: Break Down and Implement

**In the chat**, use the `/pandawa.tasks` slash command to create an actionable task list.

```markdown
/pandawa.tasks
```

Optionally, validate the plan with `/pandawa.analyze`:

```markdown
/pandawa.analyze
```

Then, use the `/pandawa.implement` slash command to execute the plan.

```markdown
/pandawa.implement
```

## Detailed Example: Building Taskify

Here's a complete example of building a team productivity platform:

### Step 1: Define Constitution

Initialize the project's constitution to set ground rules:

```markdown
/pandawa.constitution Taskify is a "Security-First" application. All user inputs must be validated. We use a microservices architecture. Code must be fully documented.
```

### Step 2: Define Requirements with `/pandawa.specify`

```text
Develop Taskify, a team productivity platform. It should allow users to create projects, add team members,
assign tasks, comment and move tasks between boards in Kanban style. In this initial phase for this feature,
let's call it "Create Taskify," let's have multiple users but the users will be declared ahead of time, predefined.
I want five users in two different categories, one product manager and four engineers. Let's create three
different sample projects. Let's have the standard Kanban columns for the status of each task, such as "To Do,"
"In Progress," "In Review," and "Done." There will be no login for this application as this is just the very
first testing thing to ensure that our basic features are set up.
```

### Step 3: Refine the Specification

Use the `/pandawa.clarify` command to interactively resolve any ambiguities in your specification. You can also provide specific details you want to ensure are included.

```bash
/pandawa.clarify I want to clarify the task card details. For each task in the UI for a task card, you should be able to change the current status of the task between the different columns in the Kanban work board. You should be able to leave an unlimited number of comments for a particular card. You should be able to, from that task card, assign one of the valid users.
```

You can continue to refine the spec with more details using `/pandawa.clarify`:

```bash
/pandawa.clarify When you first launch Taskify, it's going to give you a list of the five users to pick from. There will be no password required. When you click on a user, you go into the main view, which displays the list of projects. When you click on a project, you open the Kanban board for that project. You're going to see the columns. You'll be able to drag and drop cards back and forth between different columns. You will see any cards that are assigned to you, the currently logged in user, in a different color from all the other ones, so you can quickly see yours. You can edit any comments that you make, but you can't edit comments that other people made. You can delete any comments that you made, but you can't delete comments anybody else made.
```

### Step 4: Validate the Spec

Validate the specification checklist using the `/pandawa.checklist` command:

```bash
/pandawa.checklist
```

### Step 5: Generate Technical Plan with `/pandawa.plan`

Be specific about your tech stack and technical requirements:

```bash
/pandawa.plan We are going to generate this using .NET Aspire, using Postgres as the database. The frontend should use Blazor server with drag-and-drop task boards, real-time updates. There should be a REST API created with a projects API, tasks API, and a notifications API.
```

### Step 6: Break Down into Tasks

Generate an actionable, dependency-ordered task list from the plan:

```bash
/pandawa.tasks
```

`/pandawa.implement` (Step 7 below) requires this `tasks.md` to exist — don't skip straight from `/pandawa.plan` to `/pandawa.implement`.

> [!TIP]
> **Tracking tasks in GitHub Issues?** If your project's git remote points to GitHub, run `/pandawa.taskstoissues` here to turn `tasks.md` into one GitHub issue per task via the GitHub MCP server. It no-ops on non-GitHub remotes (e.g. GitLab).

### Step 7: Validate and Implement

Have your AI agent audit the plan and task breakdown using `/pandawa.analyze`:

```bash
/pandawa.analyze
```

Finally, implement the solution:

```bash
/pandawa.implement
```

### Step 8: Validate Tests and Code Quality (Optional)

After implementation, generate any missing unit tests and check code quality with `/pandawa.test`:

```bash
/pandawa.test
```

You can also scope it to a specific folder or module:

```bash
/pandawa.test src/services
```

This command will:

- Detect your test framework (Jest, Vitest, pytest, etc.) and conventions
- Find source files that have no corresponding test file
- Generate missing unit tests following your project's existing patterns
- Run SonarQube-style checks for code smells, duplication, complexity, and basic security issues
- Produce a quality gate report (PASSED / FAILED)

### Step 9: Iterate with Targeted Redesigns (Optional)

Once a feature is implemented, you don't need to regenerate it from scratch to change one part of it. Use `/pandawa.redesign` to make a scoped edit to a specific form, page, endpoint, or table:

```bash
/pandawa.redesign The Projected Cost create form, follow the new design file at designs/projected-cost.png
```

This only touches the part you named, records the change in `implementation-log.md`, and creates a checkpoint you can roll back to with `git diff`/`checkout`/`reset` if the result isn't right.

## Key Principles

- **Be explicit** about what you're building and why
- **Don't focus on tech stack** during specification phase
- **Iterate and refine** your specifications before implementation
- **Validate** the plan before coding begins
- **Let the AI agent handle** the implementation details

## Next Steps

- Read the [complete methodology](https://git.neuron.id/research/pandawa/blob/main/spec-driven.md) for in-depth guidance
- Check out [more examples](https://git.neuron.id/research/pandawa/tree/main/templates) in the repository
- Explore the [source code on GitLab](https://git.neuron.id/research/pandawa)
