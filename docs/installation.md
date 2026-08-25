<div align="center">
    <img src="/media/logo_large.png" alt="Pandawa Logo" width="200" height="200"/>
</div>

# Installation Guide

## Prerequisites

- **Linux/macOS** (or Windows; PowerShell scripts now supported without WSL)
- A [supported AI coding agent](https://github.com/zasbita/pandawa/blob/main/README.md#-supported-ai-agents) — e.g. Claude Code, Gemini CLI, GitHub Copilot, Cursor, Codex CLI, and 10+ others
- [uv](https://docs.astral.sh/uv/) for package management
- [Python 3.11+](https://www.python.org/downloads/)
- [Git](https://git-scm.com/downloads)

## Installing uv

`uv` is a fast Python package and project manager. Install it before running any `uvx` commands below.

**macOS / Linux:**

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

**Windows (PowerShell):**

```powershell
powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"
```

After installation, restart your terminal (or run `source $HOME/.local/bin/env`) so the `uv` and `uvx` commands are on your `PATH`. Verify with:

```bash
uv --version
```

## Installation

### Initialize a New Project

The easiest way to get started is to initialize a new project:

```bash
uvx --from git+https://github.com/zasbita/pandawa.git pandawa init <PROJECT_NAME>
```

Or initialize in the current directory:

```bash
uvx --from git+https://github.com/zasbita/pandawa.git pandawa init .
# or use the --here flag
uvx --from git+https://github.com/zasbita/pandawa.git pandawa init --here
```

### Specify AI Agent

You can proactively specify your AI agent during initialization:

```bash
uvx --from git+https://github.com/zasbita/pandawa.git pandawa init <project_name> --ai claude
uvx --from git+https://github.com/zasbita/pandawa.git pandawa init <project_name> --ai gemini
uvx --from git+https://github.com/zasbita/pandawa.git pandawa init <project_name> --ai copilot
uvx --from git+https://github.com/zasbita/pandawa.git pandawa init <project_name> --ai codebuddy
```

### Specify Script Type (Shell vs PowerShell)

All automation scripts now have both Bash (`.sh`) and PowerShell (`.ps1`) variants.

Auto behavior:

- Windows default: `ps`
- Other OS default: `sh`
- Interactive mode: you'll be prompted unless you pass `--script`

Force a specific script type:

```bash
uvx --from git+https://github.com/zasbita/pandawa.git pandawa init <project_name> --script sh
uvx --from git+https://github.com/zasbita/pandawa.git pandawa init <project_name> --script ps
```

### Ignore Agent Tools Check

If you prefer to get the templates without checking for the right tools:

```bash
uvx --from git+https://github.com/zasbita/pandawa.git pandawa init <project_name> --ai claude --ignore-agent-tools
```

## Verification

After initialization, you should see the following commands available in your AI agent:

- `/pandawa.constitution` - Establish project governing principles
- `/pandawa.brd` - (Existing projects only) Reverse-engineer a BRD from the current codebase
- `/pandawa.specify` - Create specifications
- `/pandawa.clarify` - Resolve ambiguities in a spec
- `/pandawa.plan` - Generate implementation plans
- `/pandawa.tasks` - Break down into actionable tasks
- `/pandawa.analyze` - Cross-artifact consistency check
- `/pandawa.checklist` - Generate quality checklists
- `/pandawa.implement` - Execute the plan
- `/pandawa.test` - Generate missing tests, run quality checks, and report bugs (with a failing-test proof)
- `/pandawa.redesign` - Scoped rework of an already-implemented feature
- `/pandawa.taskstoissues` - Turn `tasks.md` into GitHub issues (GitHub remotes only)
- `/pandawa.ultimate` - Run the whole lifecycle above in one guided session

See the [Quick Start Guide](quickstart.md) for how these fit together, and the main [README's CLI Reference](https://github.com/zasbita/pandawa/blob/main/README.md#-pandawa-cli-reference) for every `pandawa` subcommand.

The `.pandawa/scripts` directory will contain both `.sh` and `.ps1` scripts.

## Troubleshooting

### Git Credential Manager on Linux

If you're having issues with Git authentication on Linux, you can install Git Credential Manager:

```bash
#!/usr/bin/env bash
set -e
echo "Downloading Git Credential Manager v2.6.1..."
wget https://github.com/git-ecosystem/git-credential-manager/releases/download/v2.6.1/gcm-linux_amd64.2.6.1.deb
echo "Installing Git Credential Manager..."
sudo dpkg -i gcm-linux_amd64.2.6.1.deb
echo "Configuring Git to use GCM..."
git config --global credential.helper manager
echo "Cleaning up..."
rm gcm-linux_amd64.2.6.1.deb
```
