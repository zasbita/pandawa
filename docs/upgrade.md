# Upgrade Guide

> You have Pandawa installed and want to upgrade to the latest version to get new features, bug fixes, or updated slash commands. This guide covers both upgrading the CLI tool and updating your project files.

---

## Quick Reference

| What to Upgrade | Command | When to Use |
| --------------- | ------- | ----------- |
| **CLI Tool Only** | `uv tool install pandawa-cli --force --from git+https://git.neuron.id/research/pandawa.git` | Get latest CLI features without touching project files |
| **Project Files** | `pandawa init --here --force --ai <your-agent>` | Update slash commands, templates, and scripts in your project |
| **Both** | Run CLI upgrade, then project update | Recommended for major version updates |

---

## Part 1: Upgrade the CLI Tool

The CLI tool (`pandawa`) is separate from your project files. Upgrade it to get the latest features and bug fixes.

### If you installed with `uv tool install`

```bash
uv tool install pandawa-cli --force --from git+https://git.neuron.id/research/pandawa.git
```

### If you use one-shot `uvx` commands

No upgrade needed—`uvx` always fetches the latest version. Just run your commands as normal:

```bash
uvx --from git+https://git.neuron.id/research/pandawa.git pandawa init --here --ai copilot
```

### Verify the upgrade

```bash
pandawa check
```

This shows installed tools and confirms the CLI is working.

---

## Part 2: Updating Project Files

When Pandawa releases new features (like new slash commands or updated templates), you need to refresh your project's Pandawa files.

### What gets updated?

Running `pandawa init --here --force` will update:

- ✅ **Slash command files** (`.claude/commands/`, `.github/prompts/`, etc.)
- ✅ **Script files** (`.pandawa/scripts/`)
- ✅ **Template files** (`.pandawa/templates/`)
- ✅ **Shared memory files** (`.pandawa/memory/`) - **⚠️ See warnings below**

### What stays safe?

These files are **never touched** by the upgrade—the template packages don't even contain them:

- ✅ **Your specifications** (`specs/001-my-feature/spec.md`, etc.) - **CONFIRMED SAFE**
- ✅ **Your implementation plans** (`specs/001-my-feature/plan.md`, `tasks.md`, etc.) - **CONFIRMED SAFE**
- ✅ **Your source code** - **CONFIRMED SAFE**
- ✅ **Your git history** - **CONFIRMED SAFE**

The `specs/` directory is completely excluded from template packages and will never be modified during upgrades.

### Update command

Run this inside your project directory:

```bash
pandawa init --here --force --ai <your-agent>
```

Replace `<your-agent>` with your AI assistant. Refer to this list of [Supported AI Agents](https://git.neuron.id/research/pandawa/blob/main/README.md#-supported-ai-agents)

**Example:**

```bash
pandawa init --here --force --ai copilot
```

### Understanding the `--force` flag

Without `--force`, the CLI warns you and asks for confirmation:

```text
Warning: Current directory is not empty (25 items)
Template files will be merged with existing content and may overwrite existing files
Proceed? [y/N]
```

With `--force`, it skips the confirmation and proceeds immediately.

**Important: Your `specs/` directory is always safe.** The `--force` flag only affects template files (commands, scripts, templates, memory). Your feature specifications, plans, and tasks in `specs/` are never included in upgrade packages and cannot be overwritten.

---

## ⚠️ Important Warnings

### 1. Constitution file will be overwritten

**Known issue:** `pandawa init --here --force` currently overwrites `.pandawa/memory/constitution.md` with the default template, erasing any customizations you made.

**Workaround:**

```bash
# 1. Back up your constitution before upgrading
cp .pandawa/memory/constitution.md .pandawa/memory/constitution-backup.md

# 2. Run the upgrade
pandawa init --here --force --ai copilot

# 3. Restore your customized constitution
mv .pandawa/memory/constitution-backup.md .pandawa/memory/constitution.md
```

Or use git to restore it:

```bash
# After upgrade, restore from git history
git restore .pandawa/memory/constitution.md
```

### 2. Custom template modifications

If you customized any templates in `.pandawa/templates/`, the upgrade will overwrite them. Back them up first:

```bash
# Back up custom templates
cp -r .pandawa/templates .pandawa/templates-backup

# After upgrade, merge your changes back manually
```

### 3. Duplicate slash commands (IDE-based agents)

Some IDE-based agents (like Kilo Code, Windsurf) may show **duplicate slash commands** after upgrading—both old and new versions appear.

**Solution:** Manually delete the old command files from your agent's folder.

**Example for Kilo Code:**

```bash
# Navigate to the agent's commands folder
cd .kilocode/rules/

# List files and identify duplicates
ls -la

# Delete old versions (example filenames - yours may differ)
rm pandawa.pandawa-old.md
rm pandawa.plan-v1.md
```

Restart your IDE to refresh the command list.

---

## Common Scenarios

### Scenario 1: "I just want new slash commands"

```bash
# Upgrade CLI (if using persistent install)
uv tool install pandawa-cli --force --from git+https://git.neuron.id/research/pandawa.git

# Update project files to get new commands
pandawa init --here --force --ai copilot

# Restore your constitution if customized
git restore .pandawa/memory/constitution.md
```

### Scenario 2: "I customized templates and constitution"

```bash
# 1. Back up customizations
cp .pandawa/memory/constitution.md /tmp/constitution-backup.md
cp -r .pandawa/templates /tmp/templates-backup

# 2. Upgrade CLI
uv tool install pandawa-cli --force --from git+https://git.neuron.id/research/pandawa.git

# 3. Update project
pandawa init --here --force --ai copilot

# 4. Restore customizations
mv /tmp/constitution-backup.md .pandawa/memory/constitution.md
# Manually merge template changes if needed
```

### Scenario 3: "I see duplicate slash commands in my IDE"

This happens with IDE-based agents (Kilo Code, Windsurf, Roo Code, etc.).

```bash
# Find the agent folder (example: .kilocode/rules/)
cd .kilocode/rules/

# List all files
ls -la

# Delete old command files
rm pandawa.old-command-name.md

# Restart your IDE
```

### Scenario 4: "I'm working on a project without Git"

If you initialized your project with `--no-git`, you can still upgrade:

```bash
# Manually back up files you customized
cp .pandawa/memory/constitution.md /tmp/constitution-backup.md

# Run upgrade
pandawa init --here --force --ai copilot --no-git

# Restore customizations
mv /tmp/constitution-backup.md .pandawa/memory/constitution.md
```

The `--no-git` flag skips git initialization but doesn't affect file updates.

---

## Using `--no-git` Flag

The `--no-git` flag tells Pandawa to **skip git repository initialization**. This is useful when:

- You manage version control differently (Mercurial, SVN, etc.)
- Your project is part of a larger monorepo with existing git setup
- You're experimenting and don't want version control yet

**During initial setup:**

```bash
pandawa init my-project --ai copilot --no-git
```

**During upgrade:**

```bash
pandawa init --here --force --ai copilot --no-git
```

### What `--no-git` does NOT do

❌ Does NOT prevent file updates
❌ Does NOT skip slash command installation
❌ Does NOT affect template merging

It **only** skips running `git init` and creating the initial commit.

### Working without Git

If you use `--no-git`, you'll need to manage feature directories manually:

**Set the `PANDAWA_FEATURE` environment variable** before using planning commands:

```bash
# Bash/Zsh
export PANDAWA_FEATURE="001-my-feature"

# PowerShell
$env:PANDAWA_FEATURE = "001-my-feature"
```

This tells Pandawa which feature directory to use when creating specs, plans, and tasks.

**Why this matters:** Without git, Pandawa can't detect your current branch name to determine the active feature. The environment variable provides that context manually.

---

## Troubleshooting

### "Slash commands not showing up after upgrade"

**Cause:** Agent didn't reload the command files.

**Fix:**

1. **Restart your IDE/editor** completely (not just reload window)
2. **For CLI-based agents**, verify files exist:

   ```bash
   ls -la .claude/commands/      # Claude Code
   ls -la .gemini/commands/       # Gemini
   ls -la .cursor/commands/       # Cursor
   ```

3. **Check agent-specific setup:**
   - Codex requires `CODEX_HOME` environment variable
   - Some agents need workspace restart or cache clearing

### "I lost my constitution customizations"

**Fix:** Restore from git or backup:

```bash
# If you committed before upgrading
git restore .pandawa/memory/constitution.md

# If you backed up manually
cp /tmp/constitution-backup.md .pandawa/memory/constitution.md
```

**Prevention:** Always commit or back up `constitution.md` before upgrading.

### "Warning: Current directory is not empty"

**Full warning message:**

```text
Warning: Current directory is not empty (25 items)
Template files will be merged with existing content and may overwrite existing files
Do you want to continue? [y/N]
```

**What this means:**

This warning appears when you run `pandawa init --here` (or `pandawa init .`) in a directory that already has files. It's telling you:

1. **The directory has existing content** - In the example, 25 files/folders
2. **Files will be merged** - New template files will be added alongside your existing files
3. **Some files may be overwritten** - If you already have Pandawa files (`.claude/`, `.pandawa/`, etc.), they'll be replaced with the new versions

**What gets overwritten:**

Only Pandawa infrastructure files:

- Agent command files (`.claude/commands/`, `.github/prompts/`, etc.)
- Scripts in `.pandawa/scripts/`
- Templates in `.pandawa/templates/`
- Memory files in `.pandawa/memory/` (including constitution)

**What stays untouched:**

- Your `specs/` directory (specifications, plans, tasks)
- Your source code files
- Your `.git/` directory and git history
- Any other files not part of Pandawa templates

**How to respond:**

- **Type `y` and press Enter** - Proceed with the merge (recommended if upgrading)
- **Type `n` and press Enter** - Cancel the operation
- **Use `--force` flag** - Skip this confirmation entirely:

  ```bash
  pandawa init --here --force --ai copilot
  ```

**When you see this warning:**

- ✅ **Expected** when upgrading an existing Pandawa project
- ✅ **Expected** when adding Pandawa to an existing codebase
- ⚠️ **Unexpected** if you thought you were creating a new project in an empty directory

**Prevention tip:** Before upgrading, commit or back up your `.pandawa/memory/constitution.md` if you customized it.

### "CLI upgrade doesn't seem to work"

Verify the installation:

```bash
# Check installed tools
uv tool list

# Should show pandawa-cli

# Verify path
which pandawa

# Should point to the uv tool installation directory
```

If not found, reinstall:

```bash
uv tool uninstall pandawa-cli
uv tool install pandawa-cli --from git+https://git.neuron.id/research/pandawa.git
```

### "Do I need to run pandawa every time I open my project?"

**Short answer:** No, you only run `pandawa init` once per project (or when upgrading).

**Explanation:**

The `pandawa` CLI tool is used for:

- **Initial setup:** `pandawa init` to bootstrap Pandawa in your project
- **Upgrades:** `pandawa init --here --force` to update templates and commands
- **Diagnostics:** `pandawa check` to verify tool installation

Once you've run `pandawa init`, the slash commands (like `/pandawa.pandawa`, `/pandawa.plan`, etc.) are **permanently installed** in your project's agent folder (`.claude/`, `.github/prompts/`, etc.). Your AI assistant reads these command files directly—no need to run `pandawa` again.

**If your agent isn't recognizing slash commands:**

1. **Verify command files exist:**

   ```bash
   # For GitHub Copilot
   ls -la .github/prompts/

   # For Claude
   ls -la .claude/commands/
   ```

2. **Restart your IDE/editor completely** (not just reload window)

3. **Check you're in the correct directory** where you ran `pandawa init`

4. **For some agents**, you may need to reload the workspace or clear cache

**Related issue:** If Copilot can't open local files or uses PowerShell commands unexpectedly, this is typically an IDE context issue, not related to `pandawa`. Try:

- Restarting VS Code
- Checking file permissions
- Ensuring the workspace folder is properly opened

---

## Version Compatibility

Pandawa follows semantic versioning for major releases. The CLI and project files are designed to be compatible within the same major version.

**Best practice:** Keep both CLI and project files in sync by upgrading both together during major version changes.

---

## Next Steps

After upgrading:

- **Test new slash commands:** Run `/pandawa.constitution` or another command to verify everything works
- **Review release notes:** Check [GitHub Releases](https://git.neuron.id/research/pandawa/releases) for new features and breaking changes
- **Update workflows:** If new commands were added, update your team's development workflows
- **Check documentation:** Visit [github.io/pandawa](https://github.github.io/pandawa/) for updated guides
