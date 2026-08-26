#!/usr/bin/env python3
# /// script
# requires-python = ">=3.11"
# dependencies = [
#     "typer",
#     "rich",
#     "platformdirs",
#     "readchar",
#     "httpx",
# ]
# ///
"""
Pandawa CLI - Setup tool for Pandawa projects

Usage:
    uvx pandawa-cli.py init <project-name>
    uvx pandawa-cli.py init .
    uvx pandawa-cli.py init --here

Or install globally:
    uv tool install --from pandawa-cli.py pandawa-cli
    pandawa init <project-name>
    pandawa init .
    pandawa init --here
"""

import os
import re
import subprocess
import sys
import zipfile
import tempfile
import shutil
import shlex
import json
from pathlib import Path
from typing import Optional, Tuple
from urllib.parse import quote, urlparse, urlunparse

import typer
import httpx
from platformdirs import user_config_dir
from rich.console import Console
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.text import Text
from rich.live import Live
from rich.align import Align
from rich.table import Table
from rich.tree import Tree
from typer.core import TyperGroup

# For cross-platform keyboard input
import readchar
import ssl
import truststore
from datetime import datetime, timezone

# The shared HTTP client + OS trust store are built LAZILY (on first network use) rather
# than at import. Commands that never touch the network (`--help`, `run`, governance
# toggles, most local ops) then don't pay ~110ms per invocation to construct a TLS-verified
# client and load the system trust store. `pandawa_cli.client` / `from pandawa_cli import client`
# still work via the module __getattr__ below, so existing call sites are unchanged.
_ssl_context = None
_http_client = None


def _get_ssl_context() -> "ssl.SSLContext":
    global _ssl_context
    if _ssl_context is None:
        _ssl_context = truststore.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
    return _ssl_context


def _get_client() -> "httpx.Client":
    global _http_client
    if _http_client is None:
        _http_client = httpx.Client(verify=_get_ssl_context())
    return _http_client


def __getattr__(name: str):
    # PEP 562: keep `pandawa_cli.client` / `pandawa_cli.ssl_context` working, but lazily.
    if name == "client":
        return _get_client()
    if name == "ssl_context":
        return _get_ssl_context()
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")

_PANDAWA_CONFIG_PATH = Path(user_config_dir("pandawa")) / "config"

def _load_saved_token() -> str | None:
    """Read GL_TOKEN from shell profile as fallback (covers legacy config too)."""
    for candidate in [Path.home() / ".zshrc", Path.home() / ".bashrc", Path.home() / ".profile", _PANDAWA_CONFIG_PATH]:
        try:
            if candidate.exists():
                for line in candidate.read_text().splitlines():
                    stripped = line.strip().removeprefix("export ")
                    if stripped.startswith("GL_TOKEN="):
                        val = stripped.split("=", 1)[1].strip().strip('"').strip("'")
                        if val:
                            return val
        except Exception:
            pass
    return None

def _save_token(token: str) -> Path | None:
    """Append export GL_TOKEN=... to the user's shell profile. Returns the profile path."""
    shell = os.environ.get("SHELL", "")
    if "zsh" in shell:
        profile = Path.home() / ".zshrc"
    elif "bash" in shell:
        profile = Path.home() / ".bashrc"
    else:
        profile = Path.home() / ".profile"
    try:
        existing = profile.read_text() if profile.exists() else ""
        # Remove any previous GL_TOKEN line to avoid duplicates
        lines = [l for l in existing.splitlines() if not l.startswith("export GL_TOKEN=")]
        lines.append(f'export GL_TOKEN="{token}"')
        profile.write_text("\n".join(lines) + "\n")
        return profile
    except Exception as e:
        console.print(f"[yellow]Warning: could not save token: {e}[/yellow]")
        return None

def _gitlab_token(cli_token: str | None = None) -> str | None:
    """Return sanitized GitLab token: cli arg > env var > saved config. Does not prompt."""
    return ((cli_token or os.getenv("GL_TOKEN") or os.getenv("GITLAB_TOKEN") or os.getenv("CI_JOB_TOKEN") or _load_saved_token() or "").strip()) or None

def _require_gitlab_token(cli_token: str | None = None) -> str:
    """Return a GitLab token, prompting the user interactively if none is found."""
    token = _gitlab_token(cli_token)
    if token:
        return token

    console.print()
    console.print(Panel(
        "A GitLab token is required to download templates from [cyan]git.neuron.id[/cyan].\n\n"
        "Create one at: [cyan]https://git.neuron.id/-/user_settings/personal_access_tokens[/cyan]\n"
        "Required scope: [bold]read_api[/bold]",
        title="[yellow]GitLab Token Required[/yellow]",
        border_style="yellow",
        padding=(1, 2),
    ))

    token = typer.prompt("Enter your GitLab Personal Access Token", hide_input=True).strip()
    if not token:
        console.print("[red]No token provided. Aborting.[/red]")
        raise typer.Exit(1)

    if typer.confirm("Save token as GL_TOKEN to your shell profile for future use?", default=True):
        profile = _save_token(token)
        if profile:
            console.print(f"[green]Token saved to[/green] {profile}")
            console.print(f"[dim]Run [cyan]source {profile}[/cyan] or open a new terminal to apply.[/dim]")

    return token

def _gitlab_auth_headers(cli_token: str | None = None) -> dict:
    """Return PRIVATE-TOKEN header dict only when a non-empty token exists."""
    token = _gitlab_token(cli_token)
    return {"PRIVATE-TOKEN": token} if token else {}

def _parse_rate_limit_headers(headers: httpx.Headers) -> dict:
    """Extract and parse GitLab rate-limit headers."""
    info = {}

    # GitLab rate-limit headers (RateLimit-* without X- prefix)
    if "RateLimit-Limit" in headers:
        info["limit"] = headers.get("RateLimit-Limit")
    if "RateLimit-Remaining" in headers:
        info["remaining"] = headers.get("RateLimit-Remaining")
    if "RateLimit-Reset" in headers:
        reset_epoch = int(headers.get("RateLimit-Reset", "0"))
        if reset_epoch:
            reset_time = datetime.fromtimestamp(reset_epoch, tz=timezone.utc)
            info["reset_epoch"] = reset_epoch
            info["reset_time"] = reset_time
            info["reset_local"] = reset_time.astimezone()

    # Retry-After header (seconds or HTTP-date)
    if "Retry-After" in headers:
        retry_after = headers.get("Retry-After")
        try:
            info["retry_after_seconds"] = int(retry_after)
        except ValueError:
            # HTTP-date format - not implemented, just store as string
            info["retry_after"] = retry_after

    return info

def _format_rate_limit_error(status_code: int, headers: httpx.Headers, url: str) -> str:
    """Format a user-friendly error message with rate-limit information."""
    rate_info = _parse_rate_limit_headers(headers)

    lines = [f"GitLab API returned status {status_code} for {url}"]
    lines.append("")

    if rate_info:
        lines.append("[bold]Rate Limit Information:[/bold]")
        if "limit" in rate_info:
            lines.append(f"  • Rate Limit: {rate_info['limit']} requests/hour")
        if "remaining" in rate_info:
            lines.append(f"  • Remaining: {rate_info['remaining']}")
        if "reset_local" in rate_info:
            reset_str = rate_info["reset_local"].strftime("%Y-%m-%d %H:%M:%S %Z")
            lines.append(f"  • Resets at: {reset_str}")
        if "retry_after_seconds" in rate_info:
            lines.append(f"  • Retry after: {rate_info['retry_after_seconds']} seconds")
        lines.append("")

    # Add troubleshooting guidance
    lines.append("[bold]Troubleshooting Tips:[/bold]")
    lines.append("  • If you're on a shared CI or corporate environment, you may be rate-limited.")
    lines.append("  • Consider using a GitLab token via --gitlab-token or the GL_TOKEN/GITLAB_TOKEN")
    lines.append("    environment variable to increase rate limits.")
    lines.append("  • Authenticated requests have higher rate limits than unauthenticated.")

    return "\n".join(lines)

# Agent configuration with name, folder, install URL, and CLI tool requirement
AGENT_CONFIG = {
    "copilot": {
        "name": "GitHub Copilot",
        "folder": ".github/",
        "install_url": None,  # IDE-based, no CLI check needed
        "requires_cli": False,
    },
    "claude": {
        "name": "Claude Code",
        "folder": ".claude/",
        "install_url": "https://docs.anthropic.com/en/docs/claude-code/setup",
        "requires_cli": True,
    },
    "gemini": {
        "name": "Gemini CLI",
        "folder": ".gemini/",
        "install_url": "https://github.com/google-gemini/gemini-cli",
        "requires_cli": True,
    },
    "cursor-agent": {
        "name": "Cursor",
        "folder": ".cursor/",
        "install_url": None,  # IDE-based
        "requires_cli": False,
    },
    "qwen": {
        "name": "Qwen Code",
        "folder": ".qwen/",
        "install_url": "https://github.com/QwenLM/qwen-code",
        "requires_cli": True,
    },
    "opencode": {
        "name": "opencode",
        "folder": ".opencode/",
        "install_url": "https://opencode.ai",
        "requires_cli": True,
    },
    "codex": {
        "name": "Codex CLI",
        "folder": ".codex/",
        "install_url": "https://github.com/openai/codex",
        "requires_cli": True,
    },
    "windsurf": {
        "name": "Windsurf",
        "folder": ".windsurf/",
        "install_url": None,  # IDE-based
        "requires_cli": False,
    },
    "kilocode": {
        "name": "Kilo Code",
        "folder": ".kilocode/",
        "install_url": None,  # IDE-based
        "requires_cli": False,
    },
    "auggie": {
        "name": "Auggie CLI",
        "folder": ".augment/",
        "install_url": "https://docs.augmentcode.com/cli/setup-auggie/install-auggie-cli",
        "requires_cli": True,
    },
    "codebuddy": {
        "name": "CodeBuddy",
        "folder": ".codebuddy/",
        "install_url": "https://www.codebuddy.ai/cli",
        "requires_cli": True,
    },
    "qoder": {
        "name": "Qoder CLI",
        "folder": ".qoder/",
        "install_url": "https://qoder.com/cli",
        "requires_cli": True,
    },
    "roo": {
        "name": "Roo Code",
        "folder": ".roo/",
        "install_url": None,  # IDE-based
        "requires_cli": False,
    },
    "q": {
        "name": "Amazon Q Developer CLI",
        "folder": ".amazonq/",
        "install_url": "https://aws.amazon.com/developer/learning/q-developer-cli/",
        "requires_cli": True,
    },
    "amp": {
        "name": "Amp",
        "folder": ".agents/",
        "install_url": "https://ampcode.com/manual#install",
        "requires_cli": True,
    },
    "shai": {
        "name": "SHAI",
        "folder": ".shai/",
        "install_url": "https://github.com/ovh/shai",
        "requires_cli": True,
    },
    "bob": {
        "name": "IBM Bob",
        "folder": ".bob/",
        "install_url": None,  # IDE-based
        "requires_cli": False,
    },
}

SCRIPT_TYPE_CHOICES = {"sh": "POSIX Shell (bash/zsh)", "ps": "PowerShell"}

# Pandawa GitHub repository (public) — primary source for templates (opsi 2: full GitHub).
DEFAULT_GITHUB_REPO = "zasbita/pandawa"
DEFAULT_GITHUB_API = "https://api.github.com"

# Pandawa private plugin marketplace (skills/agents are distributed via Claude Code
# /plugin, NOT bundled into the template). PANDAWA only POINTS to the marketplace by
# writing .claude/settings.json — it never copies plugin content.
# Note: template host migrated to GitHub (zasbita/pandawa releases), but marketplace
# still supports both GitHub and GitLab raw URLs (see _marketplace_raw_file_url).
MARKETPLACE_NAME = "pandawa"
DEFAULT_MARKETPLACE_URL = "https://github.com/zasbita/pandawa-marketplace-tooling.git"
# Fallback for private GitLab internal installs (env override PANDAWA_MARKETPLACE_URL still works)
GITLAB_MARKETPLACE_URL = "https://git.neuron.id/research/pandawa-marketplace-tooling.git"
MARKETPLACE_BASELINE_PLUGINS = ["pandawa-core"]

# Governance plugins are mutually exclusive at runtime: at most ONE may be enabled per
# project (invariant G1). Claude Code has no native plugin "type" or exclusivity, so
# Pandawa enforces it on the consumer side: `pandawa governance use` toggles enabledPlugins
# deterministically, and a project-local guard hook blocks repo edits if two are ever
# active at once. This is the known governance catalog for the default marketplace; it is
# also written to `.pandawa/governance-catalog.json` (editable) so the guard works offline.
MARKETPLACE_GOVERNANCE_PLUGINS = ["tmf-oda-constitution"]
DEFAULT_PLUGIN_CATEGORY = "skill"
GOVERNANCE_CATALOG_REL = ".pandawa/governance-catalog.json"
GOVERNANCE_GUARD_REL = ".pandawa/hooks/governance-guard.py"
GOVERNANCE_GUARD_TOOLS = "Edit|MultiEdit|Write|NotebookEdit|Bash"
def _governance_guard_command() -> str:
    """The command Claude Code runs for the governance-guard hook.

    Must invoke a Python 3 interpreter that actually EXISTS on the host. macOS ships only
    `python3` (no bare `python`), so a hard-coded `python ...` dies with
    "python: command not found" on every tool call — spamming the session AND silently
    disabling the guard (the command fails before the script is ever reached). So:
      - POSIX: resolve the interpreter at RUNTIME (`python3`, then `python`) and the script
        path via CLAUDE_PROJECT_DIR (robust to the tool call's cwd). One string, portable
        across machines regardless of which interpreter name is installed.
      - Windows: bare `python` (the standard name there; `python3` is often absent), doing
        path resolution inside Python via runpy so it stays independent of cwd and shell.
    """
    if os.name == "nt":
        return (
            "python -c \"import os,sys,runpy;"
            "sys.exit(runpy.run_path("
            "os.path.join(os.environ.get('CLAUDE_PROJECT_DIR') or os.getcwd(),"
            "'.pandawa/hooks/governance-guard.py'),"
            "run_name='__main__').get('_exit_code',0))\""
        )
    return (
        "sh -c 'exec \"$(command -v python3 || command -v python)\" "
        "\"${CLAUDE_PROJECT_DIR:-$PWD}/.pandawa/hooks/governance-guard.py\"'"
    )


GOVERNANCE_GUARD_COMMAND = _governance_guard_command()


def _is_governance_guard_command(cmd: object) -> bool:
    """True for any hook command that targets our guard script — the current one, the legacy
    relative path, or the buggy bare-`python` form. Used to migrate stale commands."""
    return isinstance(cmd, str) and "governance-guard.py" in cmd

# Project-local guard hook (stdlib-only Python). Installed by `pandawa init` / `pandawa
# governance` into .pandawa/hooks/. Reads the effective enabledPlugins (user + project)
# and the governance catalog, then:
#   - SessionStart : announces the active governance, or warns on conflict.
#   - PreToolUse   : on conflict, DENIES repo-modifying tools (hard guard) via JSON.
# Fail-open by design: any error / missing catalog -> no decision (never bricks a session).
# It always exits 0; blocking is expressed as a JSON permission decision, not an exit code,
# so a missing interpreter or stray error can never accidentally block work.
GOVERNANCE_GUARD_SCRIPT = '''#!/usr/bin/env python3
"""Pandawa governance guard (project-local Claude Code hook).

Enforces invariant G1: at most one `governance`-category plugin may be enabled in a
project's effective Claude Code settings. Managed by the Pandawa CLI; do not edit by hand
(re-run `pandawa governance` / `pandawa init` to regenerate). Catalog of governance plugins:
.pandawa/governance-catalog.json.
"""
import json
import os
import sys

BLOCKED_TOOLS = {"Edit", "MultiEdit", "Write", "NotebookEdit", "Bash"}


def _load_json(path):
    try:
        with open(path, "r", encoding="utf-8") as fh:
            return json.load(fh)
    except Exception:
        return None


def _effective_enabled_plugins(project_dir):
    """enabledPlugins merged across user + project scope (project wins)."""
    effective = {}
    paths = [
        os.path.join(os.path.expanduser("~"), ".claude", "settings.json"),
        os.path.join(project_dir, ".claude", "settings.json"),  # project last -> overrides
    ]
    for path in paths:
        data = _load_json(path) or {}
        enabled = data.get("enabledPlugins")
        if isinstance(enabled, dict):
            effective.update(enabled)
    return effective


def _active_governance(project_dir):
    catalog = _load_json(os.path.join(project_dir, ".pandawa", "governance-catalog.json"))
    if not isinstance(catalog, dict):
        return None  # no catalog -> guard disabled (fail-open)
    names = set(catalog.get("governance_plugins") or [])
    if not names:
        return None
    effective = _effective_enabled_plugins(project_dir)
    return sorted(
        key for key, val in effective.items()
        if val is True and key.split("@", 1)[0] in names
    )


def main():
    try:
        raw = sys.stdin.read()
    except Exception:
        raw = ""
    try:
        payload = json.loads(raw) if raw.strip() else {}
    except Exception:
        payload = {}

    event = payload.get("hook_event_name") or payload.get("hookEventName") or ""
    project_dir = os.environ.get("CLAUDE_PROJECT_DIR") or os.getcwd()

    active = _active_governance(project_dir)
    if active is None:
        return 0  # fail-open

    short = [k.split("@", 1)[0] for k in active]

    if event == "SessionStart":
        if len(active) == 1:
            print(f"[pandawa] Active governance: {short[0]}.")
        elif len(active) >= 2:
            print(
                "[pandawa] GOVERNANCE CONFLICT: multiple governance plugins are active "
                f"({', '.join(short)}). Only one is allowed. Run `pandawa governance disable` "
                "then `pandawa governance use <name>` and restart Claude Code. "
                "Repository-modifying tools are blocked until this is resolved."
            )
        return 0

    if event == "PreToolUse" and len(active) >= 2:
        tool = payload.get("tool_name") or payload.get("toolName") or ""
        if tool in BLOCKED_TOOLS:
            reason = (
                f"Pandawa governance guard: {len(active)} governance plugins are active "
                f"({', '.join(short)}); exactly one is allowed. Resolve with "
                "`pandawa governance disable` then `pandawa governance use <name>`, and restart "
                "Claude Code before modifying the repository."
            )
            print(json.dumps({
                "hookSpecificOutput": {
                    "hookEventName": "PreToolUse",
                    "permissionDecision": "deny",
                    "permissionDecisionReason": reason,
                },
                "decision": "block",
                "reason": reason,
            }))
        return 0

    return 0


if __name__ == "__main__":
    sys.exit(main())
'''

# Baseline "loose" guardrails: deny ONLY clearly-dangerous actions; everything else is
# left at Claude Code's default. Written to .claude/settings.json by `pandawa init` (Claude
# only). Deny rules always win over allow (deny-first). Skip with --no-guardrails.
BASELINE_DENY_RULES = [
    "Bash(rm -rf *)",
    "Bash(git push --force *)",
    "Bash(git push --force-with-lease *)",
    "Read(.env)", "Read(**/.env)", "Read(**/.env.*)",
    "Read(**/*.pem)", "Read(~/.ssh/**)", "Read(~/.aws/**)",
    "Write(.env)", "Write(**/.env)",
]

# Starter project-context file for agents. Human-written context is more reliable than
# auto-generated, so this is a TEMPLATE to fill in — `pandawa init` never overwrites an
# existing CLAUDE.md.
CLAUDE_MD_TEMPLATE = """# CLAUDE.md

Project context for AI agents (Claude Code reads this automatically). Fill in the
sections below — human-written context is more reliable than auto-generated.

## Overview
<!-- What this project/app is and its purpose. -->

## Architecture
<!-- Key modules, how they fit together, important data/execution flows. -->

## Conventions
<!-- Naming, structure, patterns to follow; libraries/frameworks in use. -->

## Build, run, test
<!-- Exact commands to build, run, and test. -->

## Risky / sensitive areas
<!-- Fragile code, hidden business rules, things to be careful with (esp. legacy). -->

## How agents should work here
- Discovery-first: read and confirm understanding before changing code.
- Keep changes in scope; state what is OUT OF SCOPE; verify end-to-end.
- Prefer the smallest viable change; ask for approval on the diff.
"""

# Offline/bootstrap fallback for domain profiles. This is NOT the source of truth for what
# profiles exist — that's `profiles.json` on the `main` branch of pandawa-marketplace-tooling
# (see `fetch_profile_index`/`refresh_profile_catalog` below), fetched live via the GitLab
# API with no CLI release or packaging step involved. Profiles live in that repo (not this
# one) alongside plugins — one contribution flow, one CI validation job, one CODEOWNERS gate
# for both. A contributor adding a new profile adds their profiles/<x>/profile.json plus one
# entry in profiles.json there — this dict never needs touching; it only keeps the CLI usable
# offline / before a first refresh, and seeds the static `--profile` help text (which can't
# reflect a live catalog — Typer builds it at import time, before any refresh could run).
# `path` is the profile's folder relative to that repo's root — where its content is fetched
# from.
_PROFILE_SEED = {
    "tmforum-oda": {
        "name": "TM Forum ODA Constitution",
        "description": "TM Forum ODA Reusable Constitution Framework for enterprise telco/ODA solutions",
        "path": "profiles/tmforum-oda",
    },
    "tmforum-oda-door-v3": {
        "name": "TM Forum ODA Design DOOR v3",
        "description": "ODA Constitution + DOOR V3 Design System — NestJS, CQRS, React MFE, Module Federation",
        "path": "profiles/tmforum-oda-door-v3",
    },
}

_PROFILE_LOCAL_PATHS_FILE = Path(user_config_dir("pandawa")) / "profile-paths.json"


def _get_profile_local_path(profile_key: str) -> "Path | None":
    """Return a local directory path for the given profile, or None to trigger download.

    Priority:
    1. User-saved path via `pandawa profile set-local`
    2. `local_path_default` baked into _PROFILE_SEED (machine-specific default)
    3. None → caller falls back to GitLab download
    """
    if _PROFILE_LOCAL_PATHS_FILE.exists():
        try:
            saved = json.loads(_PROFILE_LOCAL_PATHS_FILE.read_text())
            if profile_key in saved:
                p = Path(saved[profile_key])
                if p.is_dir():
                    return p
        except Exception:
            pass
    default = _PROFILE_SEED.get(profile_key, {}).get("local_path_default")
    if default:
        p = Path(default)
        if p.is_dir():
            return p
    return None


# Machine-global cache of the live profile catalog (mirrors _PROFILE_LOCAL_PATHS_FILE's
# scope): profile selection in `init` happens before any project directory exists, and
# `profile list`/`refresh` are explicitly project-agnostic, so this can't live under a
# project's .pandawa/ the way the governance catalog does.
_PROFILE_CATALOG_FILE = Path(user_config_dir("pandawa")) / "profile-catalog.json"
# The AUTO refresh (before `profile list` / `init` / TUI) is throttled to this age so repeated
# runs don't each pay a fresh network round-trip. Explicit `pandawa profile refresh` always
# fetches (bypasses this), so freshness is never lost — only deferred.
_PROFILE_CATALOG_TTL_SECONDS = 600


def _effective_profile_config() -> dict:
    """`_PROFILE_SEED` merged with the cached live catalog (cache wins field-by-field).

    Merges per-field rather than replacing each profile's dict wholesale: a cache entry
    written by an older CLI version (or any future fetch hiccup) that's missing `path` must
    not wipe out a `path` already known from the seed — only fields the cache actually
    provides override the seed.
    """
    config = {pid: dict(cfg) for pid, cfg in _PROFILE_SEED.items()}
    try:
        data = json.loads(_PROFILE_CATALOG_FILE.read_text(encoding="utf-8"))
        for entry in data.get("profiles", []):
            pid = entry.get("id")
            if not pid:
                continue
            merged = config.get(pid, {})
            if entry.get("name"):
                merged["name"] = entry["name"]
            merged.setdefault("name", pid)
            if entry.get("description"):
                merged["description"] = entry["description"]
            merged.setdefault("description", "")
            if entry.get("path"):
                merged["path"] = entry["path"]
            if entry.get("version"):
                merged["version"] = entry["version"]
            merged.setdefault("version", None)
            config[pid] = merged
    except (FileNotFoundError, json.JSONDecodeError, OSError, AttributeError, TypeError):
        pass
    return config


def _fetch_repo_json_file(file_path: str, *, url: "str | None" = None, ref: str = "main",
                          cli_token: "str | None" = None, client: "httpx.Client | None" = None,
                          timeout: float = 10.0):
    """Fetch and parse one small JSON file from a git repo at `ref`, or None on failure.
    Defaults to the pandawa marketplace repo (same env-override precedence as skill/governance
    fetches: PANDAWA_MARKETPLACE_URL, then DEFAULT_MARKETPLACE_URL)."""
    url = url or os.getenv("PANDAWA_MARKETPLACE_URL") or DEFAULT_MARKETPLACE_URL
    api_url = _marketplace_raw_file_url(url, file_path=file_path, ref=ref)
    if not api_url:
        return None
    http = client or _get_client()
    if http is None:
        return None
    try:
        resp = http.get(api_url, timeout=timeout, follow_redirects=True, headers=_gitlab_auth_headers(cli_token))
        if resp.status_code != 200:
            return None
        return resp.json()
    except Exception:
        return None


def fetch_profile_index(*, url: "str | None" = None, ref: str = "main", cli_token: "str | None" = None,
                        client: "httpx.Client | None" = None, timeout: float = 10.0) -> "list[dict] | None":
    """Fetch the live profile index from `profiles.json` on pandawa-marketplace-tooling's `ref`.

    That file is a hand-maintained, git-committed registration list ({id, path} — mirrors how
    a marketplace plugin registers one line in marketplace.json; profiles live in that same
    repo, alongside plugins, as a separate top-level concept — not a Claude-plugin construct,
    just sharing the same repo/CI/CODEOWNERS gate). This is the live, authoritative "what
    profiles exist", with zero CLI release/packaging step involved: a contributor adds
    profiles/<x>/profile.json and one entry here, and it's fetchable the moment it merges to
    `main`.

    Returns a list of {id, name, description, path, version} (name/description/version are
    fetched per-profile from each profile's own profile.json, best-effort — a profile whose
    profile.json can't be fetched still gets included with `name` falling back to its id and
    `version` as None), or None if the index itself is unreachable (offline, bad JSON) so
    callers fall back to the cached/offline seed.
    """
    index = _fetch_repo_json_file("profiles.json", url=url, ref=ref, cli_token=cli_token, client=client, timeout=timeout)
    if not isinstance(index, list):
        return None
    entries = [e for e in index if isinstance(e, dict) and e.get("id") and e.get("path")]
    if not entries:
        return []

    # Fetch each profile's small profile.json CONCURRENTLY instead of serially — this is the
    # per-profile round-trip that dominated `profile list` / `init` / TUI latency (N sequential
    # HTTPS calls to the marketplace). Same requests, same timeout, identical results/order;
    # only the wall-clock changes (~N x latency -> ~1 x latency). httpx.Client is safe for
    # concurrent use across threads.
    from concurrent.futures import ThreadPoolExecutor

    def _fetch_entry(entry):
        pid, path = entry["id"], entry["path"]
        meta = _fetch_repo_json_file(f"{path}/profile.json", url=url, ref=ref, cli_token=cli_token, client=client, timeout=timeout)
        name = meta.get("name") if isinstance(meta, dict) else None
        description = meta.get("description") if isinstance(meta, dict) else None
        version = meta.get("version") if isinstance(meta, dict) else None
        return {"id": pid, "path": path, "name": name or pid, "description": description or "", "version": version}

    with ThreadPoolExecutor(max_workers=min(8, len(entries))) as pool:
        return list(pool.map(_fetch_entry, entries))  # map preserves input order


def refresh_profile_catalog(*, url: "str | None" = None, ref: str = "main", cli_token: "str | None" = None,
                            client: "httpx.Client | None" = None) -> "list[dict] | None":
    """Rebuild the local profile catalog cache from pandawa-marketplace-tooling (authoritative).

    Decouples the profile catalog from CLI releases: a contributor adds profiles/<x>/
    profile.json plus one entry in profiles.json there, and it shows up here as soon as
    it merges to `main` — no CLI code change, no packaging, no release needed. Returns the new
    list, or None if unreachable (caller keeps the existing cached catalog).
    """
    profiles = fetch_profile_index(url=url, ref=ref, cli_token=cli_token, client=client)
    if profiles is None:
        return None
    _PROFILE_CATALOG_FILE.parent.mkdir(parents=True, exist_ok=True)
    _PROFILE_CATALOG_FILE.write_text(json.dumps({"profiles": profiles}, indent=2) + "\n", encoding="utf-8")
    return profiles


def _auto_refresh_profile_catalog() -> None:
    """Best-effort profile catalog refresh: never prompts, silently ignores failure (offline/
    no token) so commands keep working. Skips the network entirely when the cached catalog was
    refreshed within the last _PROFILE_CATALOG_TTL_SECONDS, so repeated `profile list` / `init`
    / TUI opens don't each pay a fresh N+1 round-trip. This throttles ONLY the automatic path;
    explicit `pandawa profile refresh` calls refresh_profile_catalog() directly and always fetches."""
    try:
        import time
        cache = _PROFILE_CATALOG_FILE
        if cache.exists() and (time.time() - cache.stat().st_mtime) < _PROFILE_CATALOG_TTL_SECONDS:
            return  # cache is fresh enough — skip the network
        refresh_profile_catalog()
    except Exception:
        pass


# Maps ai_assistant key → the instruction file that agent always loads as main context.
_AGENT_INSTRUCTION_FILES: dict[str, str] = {
    "claude": "CLAUDE.md",
    "gemini": "GEMINI.md",
    "qwen": "QWEN.md",
    "codebuddy": "CODEBUDDY.md",
    "qoder": "QODER.md",
    "shai": "SHAI.md",
    "copilot": ".github/agents/copilot-instructions.md",
    "cursor-agent": ".cursor/rules/pandawa-rules.mdc",
    "windsurf": ".windsurf/rules/pandawa-rules.md",
    "kilocode": ".kilocode/rules/pandawa-rules.md",
    "auggie": ".augment/rules/pandawa-rules.md",
    "roo": ".roo/rules/pandawa-rules.md",
    "opencode": "AGENTS.md",
    "codex": "AGENTS.md",
    "amp": "AGENTS.md",
    "q": "AGENTS.md",
    "bob": "AGENTS.md",
}

CLAUDE_LOCAL_PATH = Path.home() / ".claude" / "local" / "claude"

BANNER = r"""
 ██████╗  █████╗ ███╗   ██╗██████╗  █████╗ ██╗    ██╗ █████╗
 ██╔══██╗██╔══██╗████╗  ██║██╔══██╗██╔══██╗██║    ██║██╔══██╗
 ██████╔╝███████║██╔██╗ ██║██████╔╝███████║██║ █╗ ██║███████║
 ██╔═══╝ ██╔══██║██║╚██╗██║██╔══██╗██╔══██║██║███╗██║██╔══██║
 ██║     ██║  ██║██║ ╚████║██████╔╝██║  ██║╚███╔███╔╝██║  ██║
 ╚═╝     ╚═╝  ╚═╝╚═╝  ╚═══╝╚═════╝ ╚═╝  ╚═╝ ╚══╝╚══╝ ╚═╝  ╚═╝
"""

TAGLINE = "Pandawa - Spec-Driven Agentic Toolkit"
class StepTracker:
    """Track and render hierarchical steps without emojis, similar to Claude Code tree output.
    Supports live auto-refresh via an attached refresh callback.
    """
    def __init__(self, title: str):
        self.title = title
        self.steps = []  # list of dicts: {key, label, status, detail}
        self.status_order = {"pending": 0, "running": 1, "done": 2, "error": 3, "skipped": 4}
        self._refresh_cb = None  # callable to trigger UI refresh

    def attach_refresh(self, cb):
        self._refresh_cb = cb

    def add(self, key: str, label: str):
        if key not in [s["key"] for s in self.steps]:
            self.steps.append({"key": key, "label": label, "status": "pending", "detail": ""})
            self._maybe_refresh()

    def start(self, key: str, detail: str = ""):
        self._update(key, status="running", detail=detail)

    def complete(self, key: str, detail: str = ""):
        self._update(key, status="done", detail=detail)

    def error(self, key: str, detail: str = ""):
        self._update(key, status="error", detail=detail)

    def skip(self, key: str, detail: str = ""):
        self._update(key, status="skipped", detail=detail)

    def _update(self, key: str, status: str, detail: str):
        for s in self.steps:
            if s["key"] == key:
                s["status"] = status
                if detail:
                    s["detail"] = detail
                self._maybe_refresh()
                return

        self.steps.append({"key": key, "label": key, "status": status, "detail": detail})
        self._maybe_refresh()

    def _maybe_refresh(self):
        if self._refresh_cb:
            try:
                self._refresh_cb()
            except Exception:
                pass

    def render(self):
        tree = Tree(f"[cyan]{self.title}[/cyan]", guide_style="grey50")
        for step in self.steps:
            label = step["label"]
            detail_text = step["detail"].strip() if step["detail"] else ""

            status = step["status"]
            if status == "done":
                symbol = "[green]●[/green]"
            elif status == "pending":
                symbol = "[green dim]○[/green dim]"
            elif status == "running":
                symbol = "[cyan]○[/cyan]"
            elif status == "error":
                symbol = "[red]●[/red]"
            elif status == "skipped":
                symbol = "[yellow]○[/yellow]"
            else:
                symbol = " "

            if status == "pending":
                # Entire line light gray (pending)
                if detail_text:
                    line = f"{symbol} [bright_black]{label} ({detail_text})[/bright_black]"
                else:
                    line = f"{symbol} [bright_black]{label}[/bright_black]"
            else:
                # Label white, detail (if any) light gray in parentheses
                if detail_text:
                    line = f"{symbol} [white]{label}[/white] [bright_black]({detail_text})[/bright_black]"
                else:
                    line = f"{symbol} [white]{label}[/white]"

            tree.add(line)
        return tree

# ---- Process audit / timing ---------------------------------------------------------------

def _pandawa_version_str() -> str:
    try:
        import importlib.metadata
        return importlib.metadata.version("pandawa-cli")
    except Exception:
        try:
            import tomllib
            p = Path(__file__).parent.parent.parent / "pyproject.toml"
            if p.exists():
                with open(p, "rb") as f:
                    return tomllib.load(f).get("project", {}).get("version", "unknown")
        except Exception:
            pass
    return "unknown"


class ProcessTimer:
    """Tracks wall-clock timing and exit status for a CLI command."""

    def __init__(self, command: str):
        self.command = command
        self.start_time: datetime = datetime.now(timezone.utc)
        self.end_time: "datetime | None" = None
        self.status: str = "success"
        self.error: "str | None" = None

    def stop(self, status: str = "success", error: "str | None" = None) -> None:
        self.end_time = datetime.now(timezone.utc)
        self.status = status
        self.error = error

    @property
    def duration_seconds(self) -> float:
        end = self.end_time or datetime.now(timezone.utc)
        return (end - self.start_time).total_seconds()

    def fmt_duration(self) -> str:
        secs = self.duration_seconds
        if secs < 60:
            return f"{secs:.1f}s"
        mins, s = divmod(int(secs), 60)
        return f"{mins}m {s}s"


def _write_audit_log(record: dict, project_path: "str | Path | None" = None) -> "str | None":
    """Append a JSON-lines audit entry; returns log path or None on failure."""
    if project_path:
        log_dir = Path(project_path) / ".pandawa"
    else:
        log_dir = Path(user_config_dir("pandawa"))
    try:
        log_dir.mkdir(parents=True, exist_ok=True)
        log_path = log_dir / "audit.log"
        with open(log_path, "a", encoding="utf-8") as f:
            f.write(json.dumps(record, default=str) + "\n")
        return str(log_path)
    except Exception:
        return None


def show_audit_panel(
    timer: "ProcessTimer",
    *,
    agent: "str | None" = None,
    script_type: "str | None" = None,
    profile: "str | None" = None,
    project_path: "str | Path | None" = None,
    tracker: "StepTracker | None" = None,
    usage: "dict | None" = None,
    model_usage: "dict | None" = None,
    total_cost: "float | None" = None,
    extra: "dict | None" = None,
) -> None:
    """Print an audit summary panel and append a JSON-lines log entry."""
    import platform as _pl

    start_str = timer.start_time.strftime("%Y-%m-%d %H:%M:%S UTC")
    end_str = (timer.end_time or datetime.now(timezone.utc)).strftime("%Y-%m-%d %H:%M:%S UTC")

    steps_done = steps_failed = steps_skipped = 0
    if tracker:
        for s in tracker.steps:
            st = s["status"]
            if st == "done":
                steps_done += 1
            elif st == "error":
                steps_failed += 1
            elif st == "skipped":
                steps_skipped += 1

    # Derive model name from model_usage keys (e.g. {"claude-sonnet-4-6": {...}})
    model_name: "str | None" = None
    if model_usage and isinstance(model_usage, dict):
        model_name = next(iter(model_usage), None)

    pandawa_ver = _pandawa_version_str()
    python_ver = _pl.python_version()
    platform_str = f"{_pl.system()} {_pl.machine()}"
    cwd = str(Path.cwd())
    status_icon = "[green]✓ success[/green]" if timer.status == "success" else f"[red]✗ {timer.status}[/red]"

    W = 13

    def row(label: str, value: str) -> str:
        return f"[dim]{label:<{W}}[/dim] {value}"

    lines = [
        row("Command", timer.command),
        row("Status", status_icon),
        "",
        row("Start", f"[bright_black]{start_str}[/bright_black]"),
        row("End", f"[bright_black]{end_str}[/bright_black]"),
        row("Duration", f"[cyan]{timer.fmt_duration()}[/cyan]"),
        "",
    ]

    # Token section — real data when available, N/A otherwise
    if usage and isinstance(usage, dict):
        inp = usage.get("input_tokens", 0)
        out = usage.get("output_tokens", 0)
        cache_read = usage.get("cache_read_input_tokens", 0)
        cache_new = usage.get("cache_creation_input_tokens", 0)
        lines.append(row("Input tokens", f"[cyan]{inp:,}[/cyan]"))
        lines.append(row("Output tokens", f"[cyan]{out:,}[/cyan]"))
        if cache_read:
            lines.append(row("Cache hit", f"[green]{cache_read:,}[/green] [dim](saved)[/dim]"))
        if cache_new:
            lines.append(row("Cache write", f"[yellow]{cache_new:,}[/yellow]"))
        if total_cost is not None:
            lines.append(row("Cost (USD)", f"[cyan]${total_cost:.6f}[/cyan]"))
    else:
        lines.append(row("Tokens", "[dim]— (pandawa makes no LLM calls)[/dim]"))

    if model_name or agent or script_type or profile:
        lines.append("")
        if model_name:
            lines.append(row("Model", f"[cyan]{model_name}[/cyan]"))
        if agent:
            lines.append(row("AI Agent", f"[cyan]{agent}[/cyan]"))
        if script_type:
            lines.append(row("Script Type", script_type))
        if profile:
            lines.append(row("Profile", profile))

    if tracker and (steps_done + steps_failed + steps_skipped) > 0:
        lines.append("")
        parts = [f"[green]{steps_done} done[/green]"]
        parts.append(f"[red]{steps_failed} failed[/red]" if steps_failed else "[dim]0 failed[/dim]")
        parts.append(f"[yellow]{steps_skipped} skipped[/yellow]")
        lines.append(row("Steps", " · ".join(parts)))

    if extra:
        lines.append("")
        for k, v in extra.items():
            lines.append(row(str(k), str(v)))

    lines.extend([
        "",
        row("Pandawa", f"[bright_black]{pandawa_ver}[/bright_black]"),
        row("Python", f"[bright_black]{python_ver}[/bright_black]"),
        row("Platform", f"[bright_black]{platform_str}[/bright_black]"),
        row("CWD", f"[bright_black]{cwd}[/bright_black]"),
    ])

    if timer.error:
        lines.extend(["", row("Error", f"[red]{timer.error}[/red]")])

    record: dict = {
        "command": timer.command,
        "status": timer.status,
        "start_time": start_str,
        "end_time": end_str,
        "duration_seconds": round(timer.duration_seconds, 2),
        "agent": agent,
        "model": model_name,
        "script_type": script_type,
        "profile": profile,
        "project_path": str(project_path) if project_path else None,
        "steps_done": steps_done,
        "steps_failed": steps_failed,
        "steps_skipped": steps_skipped,
        "tokens": {
            "input": usage.get("input_tokens") if usage else None,
            "output": usage.get("output_tokens") if usage else None,
            "cache_read": usage.get("cache_read_input_tokens") if usage else None,
            "cache_write": usage.get("cache_creation_input_tokens") if usage else None,
        } if usage else None,
        "cost_usd": total_cost,
        "pandawa_version": pandawa_ver,
        "python_version": python_ver,
        "platform": platform_str,
        "cwd": cwd,
        "error": timer.error,
    }
    if extra:
        record.update({k: v for k, v in extra.items()})

    log_path = _write_audit_log(record, project_path)
    if log_path:
        lines.extend(["", row("Log", f"[bright_black]{log_path}[/bright_black]")])

    border = "green" if timer.status == "success" else "red"
    console.print()
    console.print(Panel(
        "\n".join(lines),
        title="[bold]Process Audit[/bold]",
        border_style=border,
        padding=(1, 2),
    ))

def get_key():
    """Get a single keypress in a cross-platform way using readchar."""
    key = readchar.readkey()

    if key == readchar.key.UP or key == readchar.key.CTRL_P:
        return 'up'
    if key == readchar.key.DOWN or key == readchar.key.CTRL_N:
        return 'down'

    if key == readchar.key.ENTER:
        return 'enter'

    if key == readchar.key.ESC:
        return 'escape'

    if key == readchar.key.CTRL_C:
        raise KeyboardInterrupt

    return key

def select_with_arrows(options: dict, prompt_text: str = "Select an option", default_key: str = None) -> str:
    """
    Interactive selection using arrow keys with Rich Live display.
    
    Args:
        options: Dict with keys as option keys and values as descriptions
        prompt_text: Text to show above the options
        default_key: Default option key to start with
        
    Returns:
        Selected option key
    """
    option_keys = list(options.keys())
    if default_key and default_key in option_keys:
        selected_index = option_keys.index(default_key)
    else:
        selected_index = 0

    selected_key = None

    def create_selection_panel():
        """Create the selection panel with current selection highlighted."""
        table = Table.grid(padding=(0, 2))
        table.add_column(style="cyan", justify="left", width=3)
        table.add_column(style="white", justify="left")

        for i, key in enumerate(option_keys):
            if i == selected_index:
                table.add_row("▶", f"[cyan]{key}[/cyan] [dim]({options[key]})[/dim]")
            else:
                table.add_row(" ", f"[cyan]{key}[/cyan] [dim]({options[key]})[/dim]")

        table.add_row("", "")
        table.add_row("", "[dim]Use ↑/↓ to navigate, Enter to select, Esc to cancel[/dim]")

        return Panel(
            table,
            title=f"[bold]{prompt_text}[/bold]",
            border_style="cyan",
            padding=(1, 2)
        )

    console.print()

    def run_selection_loop():
        nonlocal selected_key, selected_index
        with Live(create_selection_panel(), console=console, transient=True, auto_refresh=False) as live:
            while True:
                try:
                    key = get_key()
                    if key == 'up':
                        selected_index = (selected_index - 1) % len(option_keys)
                    elif key == 'down':
                        selected_index = (selected_index + 1) % len(option_keys)
                    elif key == 'enter':
                        selected_key = option_keys[selected_index]
                        break
                    elif key == 'escape':
                        console.print("\n[yellow]Selection cancelled[/yellow]")
                        raise typer.Exit(1)

                    live.update(create_selection_panel(), refresh=True)

                except KeyboardInterrupt:
                    console.print("\n[yellow]Selection cancelled[/yellow]")
                    raise typer.Exit(1)

    run_selection_loop()

    if selected_key is None:
        console.print("\n[red]Selection failed.[/red]")
        raise typer.Exit(1)

    return selected_key

console = Console()

class BannerGroup(TyperGroup):
    """Custom group that shows banner before help."""

    def format_help(self, ctx, formatter):
        # Show banner before help
        show_banner()
        super().format_help(ctx, formatter)


app = typer.Typer(
    name="pandawa",
    help="Setup tool for Pandawa spec-driven development projects",
    add_completion=False,
    invoke_without_command=True,
    cls=BannerGroup,
)

def show_banner():
    """Display the ASCII art banner."""
    banner_lines = BANNER.strip().split('\n')
    colors = ["bright_green", "green", "cyan", "bright_cyan", "white", "bright_white"]

    styled_banner = Text()
    for i, line in enumerate(banner_lines):
        color = colors[i % len(colors)]
        styled_banner.append(line + "\n", style=color)

    console.print(Align.center(styled_banner))
    console.print(Align.center(Text(TAGLINE, style="italic bright_yellow")))
    console.print()

@app.callback()
def callback(ctx: typer.Context):
    """Launch the interactive TUI when invoked with no subcommand (in a terminal);
    fall back to the banner + hint when not attached to a terminal (CI, pipes, scripts)."""
    _auto_migrate_governance_guard(Path.cwd())
    if ctx.invoked_subcommand is None and "--help" not in sys.argv and "-h" not in sys.argv:
        if sys.stdin.isatty() and sys.stdout.isatty():
            from pandawa_cli.tui.app import PandawaTUIApp
            PandawaTUIApp(project_path=Path.cwd()).run()
            raise typer.Exit(0)
        show_banner()
        console.print(Align.center("[dim]Run 'pandawa --help' for usage information[/dim]"))
        console.print()

def run_command(cmd: list[str], check_return: bool = True, capture: bool = False, shell: bool = False) -> Optional[str]:
    """Run a shell command and optionally capture output."""
    try:
        if capture:
            result = subprocess.run(cmd, check=check_return, capture_output=True, text=True, shell=shell)
            return result.stdout.strip()
        else:
            subprocess.run(cmd, check=check_return, shell=shell)
            return None
    except subprocess.CalledProcessError as e:
        if check_return:
            console.print(f"[red]Error running command:[/red] {' '.join(cmd)}")
            console.print(f"[red]Exit code:[/red] {e.returncode}")
            if hasattr(e, 'stderr') and e.stderr:
                console.print(f"[red]Error output:[/red] {e.stderr}")
            raise
        return None

def check_tool(tool: str, tracker: StepTracker = None) -> bool:
    """Check if a tool is installed. Optionally update tracker.
    
    Args:
        tool: Name of the tool to check
        tracker: Optional StepTracker to update with results
        
    Returns:
        True if tool is found, False otherwise
    """
    # Special handling for Claude CLI after `claude migrate-installer`
    # See: https://github.com/github/pandawa/issues/123
    # The migrate-installer command REMOVES the original executable from PATH
    # and creates an alias at ~/.claude/local/claude instead
    # This path should be prioritized over other claude executables in PATH
    if tool == "claude":
        if CLAUDE_LOCAL_PATH.exists() and CLAUDE_LOCAL_PATH.is_file():
            if tracker:
                tracker.complete(tool, "available")
            return True
    
    found = shutil.which(tool) is not None
    
    if tracker:
        if found:
            tracker.complete(tool, "available")
        else:
            tracker.error(tool, "not found")
    
    return found

def is_git_repo(path: Path = None) -> bool:
    """Check if the specified path is inside a git repository."""
    if path is None:
        path = Path.cwd()
    
    if not path.is_dir():
        return False

    try:
        # Use git command to check if inside a work tree
        subprocess.run(
            ["git", "rev-parse", "--is-inside-work-tree"],
            check=True,
            capture_output=True,
            cwd=path,
        )
        return True
    except (subprocess.CalledProcessError, FileNotFoundError):
        return False

def init_git_repo(project_path: Path, quiet: bool = False) -> Tuple[bool, Optional[str]]:
    """Initialize a git repository in the specified path.
    
    Args:
        project_path: Path to initialize git repository in
        quiet: if True suppress console output (tracker handles status)
    
    Returns:
        Tuple of (success: bool, error_message: Optional[str])
    """
    try:
        original_cwd = Path.cwd()
        os.chdir(project_path)
        if not quiet:
            console.print("[cyan]Initializing git repository...[/cyan]")
        subprocess.run(["git", "init"], check=True, capture_output=True, text=True)
        subprocess.run(["git", "add", "."], check=True, capture_output=True, text=True)
        subprocess.run(["git", "commit", "-m", "Initial commit from Pandawa template"], check=True, capture_output=True, text=True)
        if not quiet:
            console.print("[green]✓[/green] Git repository initialized")
        return True, None

    except subprocess.CalledProcessError as e:
        error_msg = f"Command: {' '.join(e.cmd)}\nExit code: {e.returncode}"
        if e.stderr:
            error_msg += f"\nError: {e.stderr.strip()}"
        elif e.stdout:
            error_msg += f"\nOutput: {e.stdout.strip()}"
        
        if not quiet:
            console.print(f"[red]Error initializing git repository:[/red] {e}")
        return False, error_msg
    finally:
        os.chdir(original_cwd)

def handle_vscode_settings(sub_item, dest_file, rel_path, verbose=False, tracker=None) -> None:
    """Handle merging or copying of .vscode/settings.json files."""
    def log(message, color="green"):
        if verbose and not tracker:
            console.print(f"[{color}]{message}[/] {rel_path}")

    try:
        with open(sub_item, 'r', encoding='utf-8') as f:
            new_settings = json.load(f)

        if dest_file.exists():
            merged = merge_json_files(dest_file, new_settings, verbose=verbose and not tracker)
            with open(dest_file, 'w', encoding='utf-8') as f:
                json.dump(merged, f, indent=4)
                f.write('\n')
            log("Merged:", "green")
        else:
            shutil.copy2(sub_item, dest_file)
            log("Copied (no existing settings.json):", "blue")

    except Exception as e:
        log(f"Warning: Could not merge, copying instead: {e}", "yellow")
        shutil.copy2(sub_item, dest_file)

def merge_json_files(existing_path: Path, new_content: dict, verbose: bool = False) -> dict:
    """Merge new JSON content into existing JSON file.

    Performs a deep merge where:
    - New keys are added
    - Existing keys are preserved unless overwritten by new content
    - Nested dictionaries are merged recursively
    - Lists and other values are replaced (not merged)

    Args:
        existing_path: Path to existing JSON file
        new_content: New JSON content to merge in
        verbose: Whether to print merge details

    Returns:
        Merged JSON content as dict
    """
    try:
        with open(existing_path, 'r', encoding='utf-8') as f:
            existing_content = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        # If file doesn't exist or is invalid, just use new content
        return new_content
    if not isinstance(existing_content, dict):
        # Valid JSON but not an object (e.g. [] or null) — treat as empty so the deep-merge
        # below doesn't crash on .items()/.copy().
        return new_content

    def deep_merge(base: dict, update: dict) -> dict:
        """Recursively merge update dict into base dict."""
        result = base.copy()
        for key, value in update.items():
            if key in result and isinstance(result[key], dict) and isinstance(value, dict):
                # Recursively merge nested dictionaries
                result[key] = deep_merge(result[key], value)
            else:
                # Add new key or replace existing value
                result[key] = value
        return result

    merged = deep_merge(existing_content, new_content)

    if verbose:
        console.print(f"[cyan]Merged JSON file:[/cyan] {existing_path.name}")

    return merged

def configure_marketplace(project_path: Path, *, url: str, name: str = MARKETPLACE_NAME, plugins: list[str] | None = None, tracker: "StepTracker | None" = None) -> Path:
    """Register the Pandawa plugin marketplace in the project's .claude/settings.json
    and enable baseline plugins.

    This is a POINTER, not a copy: it records the marketplace URL + the enabled plugins
    so Claude Code can install them via /plugin. It never bundles plugin content into the
    project. Because .claude/settings.json is version-controlled, teammates are prompted
    to install on trusting the folder — no manual /plugin commands required.
    """
    plugins = plugins or []
    settings_path = project_path / ".claude" / "settings.json"
    settings_path.parent.mkdir(parents=True, exist_ok=True)
    new_content = {
        "extraKnownMarketplaces": {
            name: {"source": {"source": "url", "url": url}}
        },
        "enabledPlugins": {f"{plugin}@{name}": True for plugin in plugins},
    }
    merged = merge_json_files(settings_path, new_content)
    with open(settings_path, "w", encoding="utf-8") as f:
        json.dump(merged, f, indent=2)
        f.write("\n")
    if tracker:
        tracker.complete("marketplace", f"{name}: {', '.join(plugins) or '(no baseline)'}")
    return settings_path

def configure_guardrails(project_path: Path, *, deny_rules: list[str], tracker: "StepTracker | None" = None) -> Path:
    """Write a baseline deny-first permission set into .claude/settings.json.

    Loose-but-safe: denies only clearly-dangerous actions and leaves everything else at
    Claude Code's default. Deny rules always take precedence over allow. Unions with any
    existing permissions.deny rather than replacing it (safe for --here on existing repos).
    """
    settings_path = project_path / ".claude" / "settings.json"
    settings_path.parent.mkdir(parents=True, exist_ok=True)
    try:
        with open(settings_path, "r", encoding="utf-8") as f:
            settings = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        settings = {}
    if not isinstance(settings, dict):
        settings = {}  # valid JSON but not an object (e.g. [] / null) — don't crash on .get()
    perms = settings.get("permissions") or {}
    deny = list(perms.get("deny") or [])
    for rule in deny_rules:
        if rule not in deny:
            deny.append(rule)
    perms["deny"] = deny
    settings["permissions"] = perms
    with open(settings_path, "w", encoding="utf-8") as f:
        json.dump(settings, f, indent=2)
        f.write("\n")
    if tracker:
        tracker.complete("guardrails", f"{len(deny)} deny rules")
    return settings_path

# ---- Governance (mutually-exclusive plugin type) ---------------------------------------

def _load_project_settings(project_path: Path) -> dict:
    """Read .claude/settings.json (project scope); {} if missing/invalid."""
    try:
        return json.loads((project_path / ".claude" / "settings.json").read_text(encoding="utf-8"))
    except (FileNotFoundError, json.JSONDecodeError, OSError):
        return {}

def governance_catalog_names(project_path: Path) -> list[str]:
    """Governance plugin names known to this project.

    The project-local catalog (.pandawa/governance-catalog.json) is the source of truth and is
    derived from the live marketplace (see `refresh_governance_catalog`), so the guard and the
    CLI stay in step as contributors add/remove governance plugins. A PRESENT catalog is
    authoritative even when empty (a marketplace with zero governance plugins); only a
    MISSING/corrupt catalog falls back to the CLI's built-in offline seed.
    """
    catalog_path = project_path / GOVERNANCE_CATALOG_REL
    try:
        data = json.loads(catalog_path.read_text(encoding="utf-8"))
    except (FileNotFoundError, json.JSONDecodeError, OSError):
        return list(MARKETPLACE_GOVERNANCE_PLUGINS)  # no catalog yet -> offline seed
    names = data.get("governance_plugins")
    if isinstance(names, list):
        return list(dict.fromkeys(str(n) for n in names))  # respect the file (even if empty)
    return list(MARKETPLACE_GOVERNANCE_PLUGINS)

def write_governance_catalog(project_path: Path, names: "list[str]", *, marketplace: str = MARKETPLACE_NAME) -> Path:
    """Write .pandawa/governance-catalog.json (replacing the governance list)."""
    catalog_path = project_path / GOVERNANCE_CATALOG_REL
    catalog_path.parent.mkdir(parents=True, exist_ok=True)
    payload = {"marketplace": marketplace, "governance_plugins": list(dict.fromkeys(str(n) for n in names))}
    catalog_path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    return catalog_path

def _marketplace_raw_file_url(git_url: str, file_path: str = ".claude-plugin/marketplace.json", ref: str = "main") -> "str | None":
    """Build raw-file URL for marketplace repo (GitHub or GitLab).

    Supports GitHub (raw.githubusercontent.com) and GitLab (api/v4). Accepts
    https (`https://host/group/repo.git`) and scp-style ssh (`git@host:group/repo.git`).
    Returns None if it cannot be parsed.
    """
    u = (git_url or "").strip()
    if u.endswith(".git"):
        u = u[:-4]
    if u.startswith("git@") and "://" not in u and ":" in u:
        host, _, path = u[len("git@"):].partition(":")
    else:
        parsed = urlparse(u)
        host, path = parsed.netloc, parsed.path.lstrip("/")
    if not host or not path:
        return None
    # GitHub → raw.githubusercontent.com/<owner>/<repo>/<ref>/<file>
    if "github.com" in host:
        # path is like zasbita/pandawa-marketplace-tooling → owner/repo
        return f"https://raw.githubusercontent.com/{path}/{ref}/{file_path}"
    # GitLab → api/v4
    return f"https://{host}/api/v4/projects/{quote(path, safe='')}/repository/files/{quote(file_path, safe='')}/raw?ref={ref}"

def fetch_marketplace_plugins(url: str, *, cli_token: "str | None" = None,
                              client: "httpx.Client | None" = None, ref: str = "main",
                              timeout: float = 10.0) -> "tuple[str, dict[str, str]] | None":
    """Fetch marketplace.json → (marketplace_name, {plugin_name: category}).

    `category` defaults to 'skill' when absent. Returns None on any failure (bad URL,
    network, auth, non-200, parse) so callers can fall back to cached/offline data.
    Tries GitHub first, fallback to GitLab if primary is GitHub and fails.
    """
    def _fetch_one(u: str):
        api_url = _marketplace_raw_file_url(u, ref=ref)
        if not api_url:
            return None
        http = client or _get_client()
        if http is None:
            return None
        # choose headers by host
        if "github.com" in (u or "") or "raw.githubusercontent.com" in api_url:
            gh_token = os.getenv("GITHUB_TOKEN") or os.getenv("GH_TOKEN")
            headers = {"Accept": "application/vnd.github.v3+json"}
            if gh_token:
                headers["Authorization"] = f"Bearer {gh_token.strip()}"
        else:
            headers = _gitlab_auth_headers(cli_token)
        try:
            resp = http.get(api_url, timeout=timeout, follow_redirects=True, headers=headers)
            if resp.status_code != 200:
                return None
            data = resp.json()
        except Exception:
            return None
        if not isinstance(data, dict):
            return None
        catalog = {}
        for p in (data.get("plugins") or []):
            if isinstance(p, dict) and p.get("name"):
                catalog[p["name"]] = p.get("category") or DEFAULT_PLUGIN_CATEGORY
        return (data.get("name") or MARKETPLACE_NAME, catalog)

    result = _fetch_one(url)
    # fallback: if GitHub default fails, try GitLab marketplace (internal)
    if result is None and url and "github.com" in url and GITLAB_MARKETPLACE_URL and GITLAB_MARKETPLACE_URL != url:
        result = _fetch_one(GITLAB_MARKETPLACE_URL)
    if result is None:
        return None
    return result

def fetch_marketplace_governance(url: str, *, cli_token: "str | None" = None,
                                 client: "httpx.Client | None" = None, ref: str = "main",
                                 timeout: float = 10.0) -> "tuple[str, list[str]] | None":
    """Fetch marketplace.json and return (marketplace_name, [governance plugin names])."""
    result = fetch_marketplace_plugins(url, cli_token=cli_token, client=client, ref=ref, timeout=timeout)
    if result is None:
        return None
    marketplace, catalog = result
    govs = [n for n, c in catalog.items() if c == "governance"]
    return (marketplace, list(dict.fromkeys(govs)))

def refresh_governance_catalog(project_path: Path, *, url: "str | None" = None,
                               cli_token: "str | None" = None, client: "httpx.Client | None" = None,
                               ref: str = "main") -> "list[str] | None":
    """Rebuild the governance catalog from the live marketplace (authoritative; prunes removed).

    Decouples the governance taxonomy from CLI releases: contributors add/remove governance
    plugins in the marketplace and this picks it up. Returns the new list, or None if the
    marketplace could not be reached/parsed (caller keeps the existing cached catalog).
    """
    url = url or os.getenv("PANDAWA_MARKETPLACE_URL") or DEFAULT_MARKETPLACE_URL
    result = fetch_marketplace_governance(url, cli_token=cli_token, client=client, ref=ref)
    if result is None:
        return None
    marketplace, names = result
    write_governance_catalog(project_path, names, marketplace=marketplace or MARKETPLACE_NAME)
    return names

def _auto_refresh_catalog(project_path: Path) -> None:
    """Best-effort catalog refresh from the marketplace: uses an env token only, never prompts,
    and silently ignores any failure (offline/no token) so commands keep working."""
    try:
        refresh_governance_catalog(project_path)
    except Exception:
        pass

# ---- claude plugin CLI bridge ----------------------------------------------------------
# Claude Code owns the local plugin store; pandawa drives content install/uninstall via its
# CLI and treats `claude plugin list` as the source of truth for "installed/local". The
# ENABLE state remains in .claude/settings.json `enabledPlugins` (what Claude Code honors
# and the guard reads), so pandawa sets that bit itself — keeping download (claude plugin)
# cleanly separate from use (enabledPlugins).

def _claude_exe() -> "str | None":
    return shutil.which("claude")

def _run_claude(args: "list[str]", *, timeout: int = 180) -> "tuple[int | None, str, str]":
    """Run `claude <args>`; return (returncode, stdout, stderr). returncode is None if the
    claude CLI is missing or the call could not be executed."""
    exe = _claude_exe()
    if not exe:
        return (None, "", "claude CLI not found on PATH")
    try:
        p = subprocess.run([exe, *args], capture_output=True, text=True, timeout=timeout)
        return (p.returncode, p.stdout or "", p.stderr or "")
    except Exception as e:
        return (None, "", str(e))

def claude_installed_plugins() -> "dict[str, bool] | None":
    """Map installed plugin name -> enabled? from `claude plugin list --json`.

    Returns None when the claude CLI is unavailable or its output can't be parsed, so callers
    degrade gracefully. Defensive about the JSON shape (array, or {installed:[...]}).
    """
    rc, out, _ = _run_claude(["plugin", "list", "--json"])
    if rc != 0 or not out.strip():
        return None
    try:
        data = json.loads(out)
    except Exception:
        return None
    items = data if isinstance(data, list) else (data.get("installed") if isinstance(data, dict) else None)
    if not isinstance(items, list):
        return None
    result: "dict[str, bool]" = {}
    for it in items:
        if not isinstance(it, dict):
            continue
        raw = it.get("name") or it.get("plugin") or it.get("id")
        if not raw:
            continue
        name = str(raw).split("@", 1)[0]
        enabled = it.get("enabled")
        result[name] = enabled if isinstance(enabled, bool) else True
    return result

def active_governance_plugins(project_path: Path) -> list[str]:
    """Governance plugin names currently enabled in the PROJECT settings.json.

    The project scope is the source of truth for "which governance is active" — there is no
    parallel pointer to drift. (The runtime guard additionally inspects user scope to catch
    a governance plugin enabled globally.)
    """
    enabled = _load_project_settings(project_path).get("enabledPlugins") or {}
    known = set(governance_catalog_names(project_path))
    return sorted(
        key.split("@", 1)[0] for key, val in enabled.items()
        if val is True and key.split("@", 1)[0] in known
    )

def configure_governance_guard(project_path: Path, *, governance_plugins: "list[str] | None" = None,
                               marketplace: str = MARKETPLACE_NAME,
                               tracker: "StepTracker | None" = None) -> Path:
    """Install/refresh the project-local governance guard. Idempotent.

    Writes three things:
      - .pandawa/hooks/governance-guard.py   the stdlib guard script
      - .pandawa/governance-catalog.json     the governance plugin catalog (editable)
      - .claude/settings.json hooks        SessionStart (announce) + PreToolUse (deny)
    Does NOT enable any governance plugin — that is an explicit `pandawa governance use`.
    """
    governance_plugins = list(MARKETPLACE_GOVERNANCE_PLUGINS) if governance_plugins is None else list(governance_plugins)

    # 1) guard script
    guard_path = project_path / GOVERNANCE_GUARD_REL
    guard_path.parent.mkdir(parents=True, exist_ok=True)
    guard_path.write_text(GOVERNANCE_GUARD_SCRIPT, encoding="utf-8")

    # 2) catalog — seed ONLY when absent. The authoritative source is the marketplace via
    #    refresh_governance_catalog(); never clobber a refreshed/edited catalog here.
    catalog_path = project_path / GOVERNANCE_CATALOG_REL
    if not catalog_path.exists():
        write_governance_catalog(project_path, governance_plugins, marketplace=marketplace)

    # 3) hooks in settings.json — merge, never duplicate our command
    settings_path = project_path / ".claude" / "settings.json"
    settings_path.parent.mkdir(parents=True, exist_ok=True)
    settings = _load_project_settings(project_path)
    hooks = settings.get("hooks") or {}

    def _ensure(event: str, matcher: "str | None"):
        groups = list(hooks.get(event) or [])
        found = False
        for group in groups:
            for hook in (group.get("hooks") or []):
                cmd = hook.get("command", "")
                if cmd == GOVERNANCE_GUARD_COMMAND:
                    found = True  # already up-to-date
                elif _is_governance_guard_command(cmd):
                    hook["command"] = GOVERNANCE_GUARD_COMMAND  # migrate legacy/buggy form
                    found = True
        if found:
            return groups
        entry = {"hooks": [{"type": "command", "command": GOVERNANCE_GUARD_COMMAND}]}
        if matcher is not None:
            entry["matcher"] = matcher
        groups.append(entry)
        return groups

    hooks["SessionStart"] = _ensure("SessionStart", None)
    hooks["PreToolUse"] = _ensure("PreToolUse", GOVERNANCE_GUARD_TOOLS)
    settings["hooks"] = hooks
    settings_path.write_text(json.dumps(settings, indent=2) + "\n", encoding="utf-8")

    if tracker:
        n_known = len(governance_catalog_names(project_path))
        tracker.complete("governance", f"guard installed ({n_known} governance plugin(s) known)")
    return settings_path

def _auto_migrate_governance_guard(project_path: Path) -> None:
    """Best-effort, silent: if this project already has a governance guard installed,
    upgrade any stale hook command to the current GOVERNANCE_GUARD_COMMAND. Covers two past
    forms: the legacy relative path (`python .pandawa/hooks/...`, which broke with "No such
    file or directory" when a tool call's cwd differed from the project root) and the
    bare-`python -c ...` form (which fails "python: command not found" on macOS, where only
    `python3` exists — spamming the session and silently disabling the guard). The current
    command resolves both the interpreter and the script path portably. Only touches projects
    that already opted into governance (guard script present); never installs it fresh, and
    never raises — a stale/corrupt settings.json here must not block any `pandawa` command.
    """
    try:
        if not (project_path / GOVERNANCE_GUARD_REL).exists():
            return
        settings = _load_project_settings(project_path)
        hooks = settings.get("hooks") or {}
        changed = False
        for event in ("SessionStart", "PreToolUse"):
            for group in (hooks.get(event) or []):
                for hook in (group.get("hooks") or []):
                    cmd = hook.get("command")
                    if _is_governance_guard_command(cmd) and cmd != GOVERNANCE_GUARD_COMMAND:
                        hook["command"] = GOVERNANCE_GUARD_COMMAND
                        changed = True
        if changed:
            settings["hooks"] = hooks
            _write_project_settings(project_path, settings)
    except Exception:
        pass

def _layers_src() -> Path:
    """Root holding the bundled skills/ and agents/ layers.

    ponytail: resolved relative to this file (repo/src layout). When installing
    from a wheel, set PANDAWA_HOME to the checkout root until layers ship as
    package data.
    """
    env = os.getenv("PANDAWA_HOME")
    if env:
        return Path(env)
    return Path(__file__).resolve().parents[2]

# Hosts with a native project-local skill directory; others read from .pandawa/skills.
_LAYER_SKILL_DIRS = {
    "claude": ".claude/skills",
    "opencode": ".opencode/skills",
}

def install_layers(project_path: Path, selected_ai: str, *, tracker: "StepTracker | None" = None) -> None:
    """Install the bundled skill registry + role agents into the project.

    Canonical copy goes to .pandawa/{skills,agents}. For hosts with a native
    skill directory (see _LAYER_SKILL_DIRS), skills are also copied there so the
    host loads them without extra configuration.
    """
    root = _layers_src()
    skills_src = root / "skills"
    agents_src = root / "agents"
    if not (skills_src / "brainstorming" / "SKILL.md").exists():
        if tracker:
            tracker.skip("layers", "bundled layers not found")
        return
    if tracker:
        tracker.start("layers")

    dst_skills = project_path / ".pandawa" / "skills"
    dst_agents = project_path / ".pandawa" / "agents"
    shutil.copytree(skills_src, dst_skills, dirs_exist_ok=True,
                    ignore=shutil.ignore_patterns("__pycache__"))
    dst_agents.mkdir(parents=True, exist_ok=True)
    for agent_md in agents_src.glob("*.md"):
        shutil.copy2(agent_md, dst_agents / agent_md.name)

    copied = 0
    native = _LAYER_SKILL_DIRS.get(selected_ai)
    if native:
        host_dir = project_path / native
        for skill_dir in sorted(dst_skills.iterdir()):
            if (skill_dir / "SKILL.md").is_file():
                shutil.copytree(skill_dir, host_dir / skill_dir.name, dirs_exist_ok=True)
                copied += 1

    detail = f"{len(list(dst_skills.iterdir()))} skills, {len(list(dst_agents.glob('*.md')))} agents"
    if native:
        detail += f"; {copied} installed to {native}"
    else:
        detail += "; no native skill dir — host reads .pandawa/"
    if tracker:
        tracker.complete("layers", detail)

def scaffold_project_context(project_path: Path, *, tracker: "StepTracker | None" = None) -> bool:
    """Write a starter CLAUDE.md (project context for agents) if one does not exist.
    Never overwrites an existing CLAUDE.md (safe for existing/legacy projects)."""
    if tracker:
        tracker.start("context")
    claude_md = project_path / "CLAUDE.md"
    if claude_md.exists():
        if tracker:
            tracker.skip("context", "CLAUDE.md already exists")
        return False
    claude_md.write_text(CLAUDE_MD_TEMPLATE, encoding="utf-8")
    if tracker:
        tracker.complete("context", "CLAUDE.md template written")
    return True

def download_template_from_gitlab(ai_assistant: str, download_dir: Path, *, script_type: str = "sh", verbose: bool = True, show_progress: bool = True, client: httpx.Client = None, debug: bool = False, gitlab_token: str = None) -> Tuple[Path, dict]:
    gitlab_host = "https://git.neuron.id"
    project_path = "research%2Fpandawa"
    if client is None:
        client = _get_client()

    if verbose:
        console.print("[cyan]Fetching latest release information...[/cyan]")
    api_url = f"{gitlab_host}/api/v4/projects/{project_path}/releases?per_page=1"

    response = client.get(
        api_url,
        timeout=30,
        follow_redirects=True,
        headers=_gitlab_auth_headers(gitlab_token),
    )
    status = response.status_code
    if status != 200:
        error_msg = _format_rate_limit_error(status, response.headers, api_url)
        if debug:
            error_msg += f"\n\n[dim]Response body (truncated 500):[/dim]\n{response.text[:500]}"
        raise RuntimeError(error_msg)
    try:
        releases = response.json()
    except ValueError as je:
        raise RuntimeError(f"Failed to parse release JSON: {je}\nRaw (truncated 400): {response.text[:400]}")
    if not releases:
        raise RuntimeError("No releases found in the repository.")
    release_data = releases[0]

    links = release_data.get("assets", {}).get("links", [])
    pattern = f"pandawa-template-{ai_assistant}-{script_type}"
    matching_assets = [
        link for link in links
        if pattern in link["name"] and link["name"].endswith(".zip")
    ]

    asset = matching_assets[0] if matching_assets else None

    if asset is None:
        asset_names = "\n".join(a.get('name', '?') for a in links) or "(no assets)"
        raise RuntimeError(
            f"No matching release asset found for '{ai_assistant}' "
            f"(pattern: '{pattern}')\n\nAvailable assets:\n{asset_names}"
        )

    download_url = asset["url"]
    filename = asset["name"]
    file_size = asset.get("size", 0)

    if verbose:
        console.print(f"[cyan]Found template:[/cyan] {filename}")
        if file_size:
            console.print(f"[cyan]Size:[/cyan] {file_size:,} bytes")
        console.print(f"[cyan]Release:[/cyan] {release_data['tag_name']}")

    zip_path = download_dir / filename
    if verbose:
        console.print(f"[cyan]Downloading template...[/cyan]")

    with client.stream(
        "GET",
        download_url,
        timeout=60,
        follow_redirects=True,
        headers=_gitlab_auth_headers(gitlab_token),
    ) as dl_response:
        if dl_response.status_code != 200:
            error_msg = _format_rate_limit_error(dl_response.status_code, dl_response.headers, download_url)
            if debug:
                error_msg += f"\n\n[dim]Response body (truncated 400):[/dim]\n{dl_response.text[:400]}"
            raise RuntimeError(error_msg)
        total_size = int(dl_response.headers.get('content-length', 0))
        with open(zip_path, 'wb') as f:
            if total_size == 0:
                for chunk in dl_response.iter_bytes(chunk_size=8192):
                    f.write(chunk)
            else:
                if show_progress:
                    with Progress(
                        SpinnerColumn(),
                        TextColumn("[progress.description]{task.description}"),
                        TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
                        console=console,
                    ) as progress:
                        task = progress.add_task("Downloading...", total=total_size)
                        downloaded = 0
                        for chunk in dl_response.iter_bytes(chunk_size=8192):
                            f.write(chunk)
                            downloaded += len(chunk)
                            progress.update(task, completed=downloaded)
                else:
                    for chunk in dl_response.iter_bytes(chunk_size=8192):
                        f.write(chunk)
    if verbose:
        console.print(f"Downloaded: {filename}")
    metadata = {
        "filename": filename,
        "size": file_size,
        "release": release_data["tag_name"],
        "asset_url": download_url
    }
    return zip_path, metadata

def download_template_from_github(ai_assistant: str, download_dir: Path, *, script_type: str = "sh", verbose: bool = True, show_progress: bool = True, client: httpx.Client = None, debug: bool = False, github_repo: str = None) -> Tuple[Path, dict]:
    """Download template zip from GitHub Releases (public, no token).

    Fetches latest release from api.github.com/repos/<repo>/releases/latest,
    picks asset matching pandawa-template-{ai}-{script}.zip.
    """
    repo = github_repo or os.getenv("PANDAWA_GITHUB_REPO") or DEFAULT_GITHUB_REPO
    if client is None:
        client = _get_client()
    if verbose:
        console.print(f"[cyan]Fetching latest release from GitHub ({repo})...[/cyan]")
    api_url = f"https://api.github.com/repos/{repo}/releases/latest"
    headers = {"Accept": "application/vnd.github.v3+json"}
    # GitHub public repo needs no auth; optionally use GITHUB_TOKEN if set
    gh_token = os.getenv("GITHUB_TOKEN") or os.getenv("GH_TOKEN")
    if gh_token:
        headers["Authorization"] = f"Bearer {gh_token.strip()}"
    response = client.get(api_url, timeout=30, follow_redirects=True, headers=headers)
    status = response.status_code
    if status != 200:
        error_msg = _format_rate_limit_error(status, response.headers, api_url)
        if debug:
            error_msg += f"\n\n[dim]Response body (truncated 500):[/dim]\n{response.text[:500]}"
        raise RuntimeError(error_msg)
    try:
        release_data = response.json()
    except ValueError as je:
        raise RuntimeError(f"Failed to parse release JSON: {je}\nRaw (truncated 400): {response.text[:400]}")
    assets = release_data.get("assets", [])
    pattern = f"pandawa-template-{ai_assistant}-{script_type}"
    matching = [a for a in assets if pattern in a.get("name","") and a["name"].endswith(".zip")]
    asset = matching[0] if matching else None
    if asset is None:
        names = "\n".join(a.get('name','?') for a in assets) or "(no assets)"
        raise RuntimeError(f"No matching release asset found for '{ai_assistant}' (pattern: '{pattern}')\n\nAvailable assets:\n{names}")
    download_url = asset.get("browser_download_url") or asset.get("url")
    filename = asset.get("name")
    file_size = asset.get("size", 0)
    if verbose:
        console.print(f"[cyan]Found template:[/cyan] {filename}")
        if file_size:
            console.print(f"[cyan]Size:[/cyan] {file_size:,} bytes")
        console.print(f"[cyan]Release:[/cyan] {release_data.get('tag_name','?')}")
        console.print(f"[cyan]Downloading template...[/cyan]")
    zip_path = download_dir / filename
    # GitHub browser_download_url redirects, no special headers needed
    dl_headers = {}
    if gh_token and "api.github.com" in download_url:
        dl_headers["Authorization"] = f"Bearer {gh_token.strip()}"
    with client.stream("GET", download_url, timeout=60, follow_redirects=True, headers=dl_headers) as dl_response:
        if dl_response.status_code != 200:
            error_msg = _format_rate_limit_error(dl_response.status_code, dl_response.headers, download_url)
            if debug:
                error_msg += f"\n\n[dim]Response body (truncated 400):[/dim]\n{dl_response.text[:400]}"
            raise RuntimeError(error_msg)
        total_size = int(dl_response.headers.get('content-length', 0))
        with open(zip_path, 'wb') as f:
            if total_size == 0:
                for chunk in dl_response.iter_bytes(chunk_size=8192):
                    f.write(chunk)
            else:
                if show_progress:
                    with Progress(SpinnerColumn(), TextColumn("[progress.description]{task.description}"), TextColumn("[progress.percentage]{task.percentage:>3.0f}%"), console=console) as progress:
                        task = progress.add_task("Downloading...", total=total_size)
                        downloaded = 0
                        for chunk in dl_response.iter_bytes(chunk_size=8192):
                            f.write(chunk); downloaded += len(chunk); progress.update(task, completed=downloaded)
                else:
                    for chunk in dl_response.iter_bytes(chunk_size=8192):
                        f.write(chunk)
    if verbose:
        console.print(f"Downloaded: {filename}")
    metadata = {"filename": filename, "size": file_size, "release": release_data.get("tag_name",""), "asset_url": download_url}
    return zip_path, metadata

def download_and_extract_template(project_path: Path, ai_assistant: str, script_type: str, is_current_dir: bool = False, *, verbose: bool = True, tracker: StepTracker | None = None, client: httpx.Client = None, debug: bool = False, gitlab_token: str = None) -> Path:
    """Download the latest release and extract it to create a new project.
    Returns project_path. Uses tracker if provided (with keys: fetch, download, extract, cleanup)
    """
    current_dir = Path.cwd()

    if tracker:
        tracker.start("fetch", "contacting GitHub API")
    # Opsi 2: GitHub primary (public), fallback to GitLab for internal compatibility
    last_exc = None
    try:
        zip_path, meta = download_template_from_github(
            ai_assistant,
            current_dir,
            script_type=script_type,
            verbose=verbose and tracker is None,
            show_progress=(tracker is None),
            client=client,
            debug=debug,
        )
        if tracker:
            tracker.complete("fetch", f"GitHub {meta['release']} ({meta['size']:,} bytes)")
            tracker.add("download", "Download template")
            tracker.complete("download", meta['filename'])
    except Exception as e_gh:
        last_exc = e_gh
        # fallback to GitLab (private) if GitHub fails
        try:
            if verbose and tracker is None:
                console.print(f"[yellow]GitHub fetch failed ({e_gh}), trying GitLab fallback...[/yellow]")
            zip_path, meta = download_template_from_gitlab(
                ai_assistant,
                current_dir,
                script_type=script_type,
                verbose=verbose and tracker is None,
                show_progress=(tracker is None),
                client=client,
                debug=debug,
                gitlab_token=gitlab_token
            )
            if tracker:
                tracker.complete("fetch", f"GitLab {meta['release']} ({meta['size']:,} bytes)")
                tracker.add("download", "Download template")
                tracker.complete("download", meta['filename'])
        except Exception as e_gl:
            if tracker:
                tracker.error("fetch", f"GitHub: {last_exc} | GitLab: {e_gl}")
            else:
                if verbose:
                    console.print(f"[red]Error downloading template (GitHub):[/red] {last_exc}")
                    console.print(f"[red]Error downloading template (GitLab):[/red] {e_gl}")
            raise last_exc from e_gl

    if tracker:
        tracker.add("extract", "Extract template")
        tracker.start("extract")
    elif verbose:
        console.print("Extracting template...")

    try:
        if not is_current_dir:
            project_path.mkdir(parents=True)

        with zipfile.ZipFile(zip_path, 'r') as zip_ref:
            zip_contents = zip_ref.namelist()
            if tracker:
                tracker.start("zip-list")
                tracker.complete("zip-list", f"{len(zip_contents)} entries")
            elif verbose:
                console.print(f"[cyan]ZIP contains {len(zip_contents)} items[/cyan]")

            if is_current_dir:
                with tempfile.TemporaryDirectory() as temp_dir:
                    temp_path = Path(temp_dir)
                    zip_ref.extractall(temp_path)

                    extracted_items = list(temp_path.iterdir())
                    if tracker:
                        tracker.start("extracted-summary")
                        tracker.complete("extracted-summary", f"temp {len(extracted_items)} items")
                    elif verbose:
                        console.print(f"[cyan]Extracted {len(extracted_items)} items to temp location[/cyan]")

                    source_dir = temp_path
                    if len(extracted_items) == 1 and extracted_items[0].is_dir():
                        source_dir = extracted_items[0]
                        if tracker:
                            tracker.add("flatten", "Flatten nested directory")
                            tracker.complete("flatten")
                        elif verbose:
                            console.print(f"[cyan]Found nested directory structure[/cyan]")

                    for item in source_dir.iterdir():
                        dest_path = project_path / item.name
                        if item.is_dir():
                            if dest_path.exists():
                                if verbose and not tracker:
                                    console.print(f"[yellow]Merging directory:[/yellow] {item.name}")
                                for sub_item in item.rglob('*'):
                                    if sub_item.is_file():
                                        rel_path = sub_item.relative_to(item)
                                        dest_file = dest_path / rel_path
                                        dest_file.parent.mkdir(parents=True, exist_ok=True)
                                        # Special handling for .vscode/settings.json - merge instead of overwrite
                                        if dest_file.name == "settings.json" and dest_file.parent.name == ".vscode":
                                            handle_vscode_settings(sub_item, dest_file, rel_path, verbose, tracker)
                                        else:
                                            shutil.copy2(sub_item, dest_file)
                            else:
                                shutil.copytree(item, dest_path)
                        else:
                            if dest_path.exists() and verbose and not tracker:
                                console.print(f"[yellow]Overwriting file:[/yellow] {item.name}")
                            shutil.copy2(item, dest_path)
                    if verbose and not tracker:
                        console.print(f"[cyan]Template files merged into current directory[/cyan]")
            else:
                zip_ref.extractall(project_path)

                extracted_items = list(project_path.iterdir())
                if tracker:
                    tracker.start("extracted-summary")
                    tracker.complete("extracted-summary", f"{len(extracted_items)} top-level items")
                elif verbose:
                    console.print(f"[cyan]Extracted {len(extracted_items)} items to {project_path}:[/cyan]")
                    for item in extracted_items:
                        console.print(f"  - {item.name} ({'dir' if item.is_dir() else 'file'})")

                if len(extracted_items) == 1 and extracted_items[0].is_dir():
                    nested_dir = extracted_items[0]
                    temp_move_dir = project_path.parent / f"{project_path.name}_temp"

                    shutil.move(str(nested_dir), str(temp_move_dir))

                    project_path.rmdir()

                    shutil.move(str(temp_move_dir), str(project_path))
                    if tracker:
                        tracker.add("flatten", "Flatten nested directory")
                        tracker.complete("flatten")
                    elif verbose:
                        console.print(f"[cyan]Flattened nested directory structure[/cyan]")

    except Exception as e:
        if tracker:
            tracker.error("extract", str(e))
        else:
            if verbose:
                console.print(f"[red]Error extracting template:[/red] {e}")
                if debug:
                    console.print(Panel(str(e), title="Extraction Error", border_style="red"))

        if not is_current_dir and project_path.exists():
            shutil.rmtree(project_path)
        raise
    else:
        if tracker:
            tracker.complete("extract")
    finally:
        if tracker:
            tracker.add("cleanup", "Remove temporary archive")

        if zip_path.exists():
            zip_path.unlink()
            if tracker:
                tracker.complete("cleanup")
            elif verbose:
                console.print(f"Cleaned up: {zip_path.name}")

    return project_path


def _profile_compliance_reference(profile_prefix: str, profile_dest: "Path | None") -> str:
    """Point at whatever compliance-checking artifact this specific profile actually ships.

    Profiles are not required to follow the same convention: `tmforum-oda` ships a
    machine-readable `_oda-compliance-matrix.json`; other profiles (e.g. `support-service`)
    document compliance purely through `validation/*.md` rule books instead. Check the
    extracted profile directory rather than assuming one profile's convention is universal.
    """
    if profile_dest is not None:
        if (profile_dest / "_oda-compliance-matrix.json").exists():
            return f"Validate all output against `{profile_prefix}/_oda-compliance-matrix.json`"
        validation_dir = profile_dest / "validation"
        if validation_dir.is_dir() and any(validation_dir.glob("*.md")):
            return f"Validate all output against the rule books in `{profile_prefix}/validation/`"
    return f"Validate all output against the compliance levels defined in `{profile_prefix}/constitution/00-index.md`"


def _profile_lint_reference(profile_prefix: str, profile_dest: "Path | None") -> "str | None":
    """Return the profile's machine-readable lint config reference, if it ships one."""
    if profile_dest is not None and (profile_dest / "_adherence.oxlintrc.json").exists():
        return f"Linting rules: `{profile_prefix}/_adherence.oxlintrc.json`"
    return None


def _profile_frontend_constitution_ref(profile_prefix: str, profile_dest: "Path | None") -> "str | None":
    """Find whichever constitution file documents frontend standards for this profile.

    Domain numbering/naming is profile-specific (tmforum-oda's frontend domain is
    `04-frontend-engineering.md`; support-service's is `05-frontend-engineering.md`) — locate it
    by pattern instead of hardcoding a filename that only matches one profile.
    """
    if profile_dest is None:
        return None
    constitution_dir = profile_dest / "constitution"
    if not constitution_dir.is_dir():
        return None
    matches = sorted(constitution_dir.glob("*frontend*.md"))
    if not matches:
        return None
    return f"{profile_prefix}/constitution/{matches[0].name}"


def _build_profile_agent_block(profile_id: str, profile_prefix: str, config: dict, profile_dest: "Path | None" = None) -> str:
    """Build the instruction block injected into the agent's always-loaded context file."""
    name = config.get("name", profile_id)
    compliance_line = _profile_compliance_reference(profile_prefix, profile_dest)
    frontend_file = _profile_frontend_constitution_ref(profile_prefix, profile_dest)
    frontend_caveat = ""
    if frontend_file:
        frontend_caveat = f"""

**Existing frontend caveat**: if this project already has its own frontend design
system (a component library already in use, not this profile's), that existing one
governs new frontend work instead of this profile's own stack — see the scope note
about existing frontend design systems in `{frontend_file}` before assuming the
profile's default component library applies."""
    return f"""---

## Domain Profile: {name}

{config.get('description', '')}

**You MUST read the following before writing any code, architecture decision, or technical plan:**

1. `{profile_prefix}/SKILL.md` — full operating instructions and per-task compliance checklist
2. The relevant constitution domain in `{profile_prefix}/constitution/` for your task — see `{profile_prefix}/constitution/00-index.md` for the full domain index
3. {compliance_line}{frontend_caveat}

See `{profile_prefix}/README.md` for the full framework overview."""


def _build_profile_constitution_block(profile_id: str, profile_prefix: str, config: dict, profile_dest: "Path | None" = None) -> str:
    """Build the constitution section pre-populated for /pandawa.plan to read."""
    name = config.get("name", profile_id)
    compliance_line = _profile_compliance_reference(profile_prefix, profile_dest)
    lint_line = _profile_lint_reference(profile_prefix, profile_dest)
    lint_suffix = f"\n{lint_line}" if lint_line else ""
    return f"""---

## Active Domain Profile: {name}

This project MUST conform to the **{name}** in `{profile_prefix}/`.

See `{profile_prefix}/constitution/00-index.md` for the full list of constitution
domains, RFC 2119 terminology, and how they depend on each other.

{compliance_line}{lint_suffix}"""


# Per-project record of which version of each installed profile is sitting in
# .pandawa/profiles/{id}/ — separate from _PROFILE_CATALOG_FILE (machine-global, "what's
# available") because this is project-specific ("what's actually installed here"). This is
# what makes an update "keliatan": `pandawa profile status` diffs this against the live catalog.
_PROFILE_LOCK_FILENAME = "profile-lock.json"


def _profile_lock_path(project_path: Path) -> Path:
    return project_path / ".pandawa" / _PROFILE_LOCK_FILENAME


def _read_profile_lock(project_path: Path) -> dict:
    """Return {"profiles": {id: {version, ref, source, installed_at}}}, or an empty dict shape
    if the lockfile doesn't exist yet or is unreadable (never raises)."""
    path = _profile_lock_path(project_path)
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        if isinstance(data, dict) and isinstance(data.get("profiles"), dict):
            return data
    except (FileNotFoundError, json.JSONDecodeError, OSError):
        pass
    return {"profiles": {}}


def _write_profile_lock_entry(project_path: Path, profile_id: str, *, version: "str | None",
                              ref: str, source: str) -> None:
    """Record the version of `profile_id` just installed/updated into this project's lockfile.

    `version` is read from the freshly extracted profile.json itself (not the cached catalog)
    so this stays correct even for --profile-path installs that never touch the catalog.
    `version` of None means the installed profile.json predates the version field — stored as
    null so `pandawa profile status` can render it as "unknown" rather than pretending it matches.
    """
    path = _profile_lock_path(project_path)
    lock = _read_profile_lock(project_path)
    lock["profiles"][profile_id] = {
        "version": version,
        "ref": ref,
        "source": source,
        "installed_at": datetime.now(timezone.utc).isoformat(),
    }
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(lock, indent=2) + "\n", encoding="utf-8")


def download_profile_archive_from_github(profile_path: str, download_dir: Path, *, ref: str = "main",
                                         verbose: bool = True, show_progress: bool = True,
                                         client: httpx.Client = None, debug: bool = False,
                                         github_repo: str = None) -> Tuple[Path, dict]:
    """Download profile folder from GitHub (public) via full repo archive."""
    repo = github_repo or os.getenv("PANDAWA_MARKETPLACE_GITHUB_REPO") or "zasbita/pandawa-marketplace-tooling"
    if client is None:
        client = _get_client()
    if verbose:
        console.print(f"[cyan]Fetching profile from GitHub:[/cyan] {profile_path} @ {ref} ({repo})")
    download_url = f"https://github.com/{repo}/archive/refs/heads/{ref}.zip"
    zip_path = download_dir / f"profile-{Path(profile_path).name}-{ref}-github.zip"
    if verbose:
        console.print("[cyan]Downloading profile (GitHub)...[/cyan]")
    headers = {}
    gh_token = os.getenv("GITHUB_TOKEN") or os.getenv("GH_TOKEN")
    if gh_token:
        headers["Authorization"] = f"Bearer {gh_token.strip()}"
    with client.stream("GET", download_url, timeout=60, follow_redirects=True, headers=headers) as dl_response:
        if dl_response.status_code != 200:
            dl_response.read()
            error_msg = _format_rate_limit_error(dl_response.status_code, dl_response.headers, download_url)
            if debug:
                error_msg += f"\n\n[dim]Response body (truncated 400):[/dim]\n{dl_response.text[:400]}"
            raise RuntimeError(f"{error_msg}\n\nNo content at '{profile_path}' on ref '{ref}' (GitHub repo {repo}).")
        total_size = int(dl_response.headers.get("content-length", 0))
        with open(zip_path, "wb") as f:
            if total_size == 0 or not show_progress:
                for chunk in dl_response.iter_bytes(chunk_size=8192):
                    f.write(chunk)
            else:
                with Progress(SpinnerColumn(), TextColumn("[progress.description]{task.description}"), TextColumn("[progress.percentage]{task.percentage:>3.0f}%"), console=console) as progress:
                    task = progress.add_task("Downloading profile...", total=total_size)
                    downloaded = 0
                    for chunk in dl_response.iter_bytes(chunk_size=8192):
                        f.write(chunk); downloaded += len(chunk); progress.update(task, completed=downloaded)
    if verbose:
        console.print(f"Downloaded: {zip_path.name} (full repo archive, will extract subpath)")
    return zip_path, {"path": profile_path, "ref": ref, "size": zip_path.stat().st_size, "github": True}

def download_profile_archive_from_gitlab(profile_path: str, download_dir: Path, *, ref: str = "main",
                                         verbose: bool = True, show_progress: bool = True,
                                         client: httpx.Client = None, debug: bool = False,
                                         gitlab_token: str = None) -> Tuple[Path, dict]:
    """Download a profile's folder straight from git — no release/packaging step involved.

    Profiles live in pandawa-marketplace-tooling (alongside plugins, as a separate top-level
    concept), not this repo. Uses GitLab's repository-archive API scoped to `profile_path`
    (e.g. `profiles/tmforum-oda-door-v3`) at `ref` (defaults to `main`), so a profile is
    installable the moment its content merges — no CLI release needs to ship first.
    """
    gitlab_host = "https://git.neuron.id"
    project_path_encoded = "research%2Fpandawa-marketplace-tooling"
    if client is None:
        client = _get_client()

    if verbose:
        console.print(f"[cyan]Fetching profile from git:[/cyan] {profile_path} @ {ref}")
    download_url = (
        f"{gitlab_host}/api/v4/projects/{project_path_encoded}/repository/archive.zip"
        f"?sha={quote(ref, safe='')}&path={quote(profile_path, safe='')}"
    )

    zip_path = download_dir / f"profile-{Path(profile_path).name}-{ref}.zip"
    if verbose:
        console.print("[cyan]Downloading profile...[/cyan]")

    with client.stream("GET", download_url, timeout=60, follow_redirects=True, headers=_gitlab_auth_headers(gitlab_token)) as dl_response:
        if dl_response.status_code != 200:
            dl_response.read()
            error_msg = _format_rate_limit_error(dl_response.status_code, dl_response.headers, download_url)
            if debug:
                error_msg += f"\n\n[dim]Response body (truncated 400):[/dim]\n{dl_response.text[:400]}"
            raise RuntimeError(
                f"{error_msg}\n\nNo content found at '{profile_path}' on ref '{ref}' — "
                "check the path in profiles.json / --profile-path is correct."
            )
        total_size = int(dl_response.headers.get("content-length", 0))
        with open(zip_path, "wb") as f:
            if total_size == 0 or not show_progress:
                for chunk in dl_response.iter_bytes(chunk_size=8192):
                    f.write(chunk)
            else:
                with Progress(SpinnerColumn(), TextColumn("[progress.description]{task.description}"), TextColumn("[progress.percentage]{task.percentage:>3.0f}%"), console=console) as progress:
                    task = progress.add_task("Downloading profile...", total=total_size)
                    downloaded = 0
                    for chunk in dl_response.iter_bytes(chunk_size=8192):
                        f.write(chunk)
                        downloaded += len(chunk)
                        progress.update(task, completed=downloaded)

    if verbose:
        console.print(f"Downloaded: {zip_path.name}")
    metadata = {"path": profile_path, "ref": ref, "size": zip_path.stat().st_size}
    return zip_path, metadata


def download_and_extract_profile(project_path: Path, profile_id: str, ai_assistant: str, *, local_path: Path | None = None, verbose: bool = True, tracker: StepTracker | None = None, client: httpx.Client = None, debug: bool = False, gitlab_token: str = None) -> Path:
    """Download and extract a domain profile into .pandawa/profiles/{profile_id}/.
    When local_path is given, copies from that directory instead of downloading.
    Returns project_path.
    """
    current_dir = Path.cwd()
    profile_dest = project_path / ".pandawa" / "profiles" / profile_id
    zip_path: Path | None = None

    if local_path is not None:
        if tracker:
            tracker.skip("profile-fetch", f"local path: {local_path}")
            tracker.add("profile-download", "Download profile")
            tracker.skip("profile-download", "local path, no download")
        elif verbose:
            console.print(f"[cyan]Using local profile source:[/cyan] {local_path}")
    else:
        profile_path = _effective_profile_config().get(profile_id, {}).get("path")
        if not profile_path:
            raise RuntimeError(
                f"Don't know where to fetch profile '{profile_id}' from (no 'path' in the "
                "profile catalog). Run `pandawa profile refresh` first, or pass --profile-path "
                "if you're testing a profile that hasn't merged to profiles.json yet."
            )
        if tracker:
            tracker.start("profile-fetch", "contacting GitHub API")
        last_exc = None
        try:
            zip_path, meta = download_profile_archive_from_github(
                profile_path, current_dir,
                verbose=verbose and tracker is None,
                show_progress=(tracker is None),
                client=client, debug=debug,
            )
            if tracker:
                tracker.complete("profile-fetch", f"GitHub {meta['path']} @ {meta['ref']} ({meta['size']:,} bytes)")
                tracker.add("profile-download", "Download profile")
                tracker.complete("profile-download", zip_path.name)
        except Exception as e_gh:
            last_exc = e_gh
            try:
                if verbose and tracker is None:
                    console.print(f"[yellow]GitHub profile fetch failed ({e_gh}), trying GitLab...[/yellow]")
                zip_path, meta = download_profile_archive_from_gitlab(
                    profile_path, current_dir,
                    verbose=verbose and tracker is None,
                    show_progress=(tracker is None),
                    client=client, debug=debug, gitlab_token=gitlab_token,
                )
                if tracker:
                    tracker.complete("profile-fetch", f"GitLab {meta['path']} @ {meta['ref']} ({meta['size']:,} bytes)")
                    tracker.add("profile-download", "Download profile")
                    tracker.complete("profile-download", zip_path.name)
            except Exception as e_gl:
                if tracker:
                    tracker.error("profile-fetch", f"GitHub: {last_exc} | GitLab: {e_gl}")
                raise last_exc from e_gl

    if tracker:
        tracker.add("profile-extract", "Extract profile")
        tracker.start("profile-extract")
    try:
        profile_dest.mkdir(parents=True, exist_ok=True)

        if local_path is not None:
            source_dir = Path(local_path)
            if not source_dir.is_dir():
                raise RuntimeError(f"Profile source path is not a directory: {local_path}")
            for item in source_dir.iterdir():
                dest = profile_dest / item.name
                if item.is_dir():
                    if dest.exists():
                        shutil.copytree(item, dest, dirs_exist_ok=True)
                    else:
                        shutil.copytree(item, dest)
                else:
                    shutil.copy2(item, dest)
        else:
            with tempfile.TemporaryDirectory() as temp_dir:
                temp_path = Path(temp_dir)
                with zipfile.ZipFile(zip_path, "r") as zip_ref:
                    zip_ref.extractall(temp_path)
                # GitLab's repository-archive API (scoped via `path=`) nests the requested
                # folder under a `<project>-<sha>/...` prefix whose exact depth isn't
                # documented — locate the profile root by its manifest instead of assuming a
                # fixed nesting depth, so this stays correct regardless of that internal layout.
                manifest = next(temp_path.rglob("profile.json"), None)
                if manifest is None:
                    raise RuntimeError(
                        f"Downloaded archive for '{profile_id}' does not contain a profile.json "
                        "— the path in profiles.json may be wrong."
                    )
                source_dir = manifest.parent
                for item in source_dir.iterdir():
                    dest = profile_dest / item.name
                    if item.is_dir():
                        if dest.exists():
                            shutil.copytree(item, dest, dirs_exist_ok=True)
                        else:
                            shutil.copytree(item, dest)
                    else:
                        shutil.copy2(item, dest)

        profile_prefix = f".pandawa/profiles/{profile_id}"
        profile_cfg = _effective_profile_config().get(profile_id, {})

        # 1. Inject into agent's main instruction file (always-loaded context).
        instruction_rel = _AGENT_INSTRUCTION_FILES.get(ai_assistant, "AGENTS.md")
        instruction_file = project_path / instruction_rel
        instruction_file.parent.mkdir(parents=True, exist_ok=True)
        profile_block = _build_profile_agent_block(profile_id, profile_prefix, profile_cfg, profile_dest)
        if instruction_file.exists():
            existing = instruction_file.read_text()
            if profile_id not in existing:
                instruction_file.write_text(existing.rstrip() + "\n\n" + profile_block + "\n")
        else:
            instruction_file.write_text(profile_block + "\n")

        # 2. Pre-populate .pandawa/memory/constitution.md so /pandawa.plan picks up profile constraints.
        constitution_file = project_path / ".pandawa" / "memory" / "constitution.md"
        constitution_file.parent.mkdir(parents=True, exist_ok=True)
        constitution_block = _build_profile_constitution_block(profile_id, profile_prefix, profile_cfg, profile_dest)
        if constitution_file.exists():
            existing = constitution_file.read_text()
            if profile_id not in existing:
                constitution_file.write_text(existing.rstrip() + "\n\n" + constitution_block + "\n")
        else:
            constitution_file.write_text(constitution_block + "\n")

        # 3. Rewrite SKILL.md paths in-place so all agents can resolve them from project root.
        skill_src = profile_dest / "SKILL.md"
        if skill_src.exists():
            skill_content = skill_src.read_text()
            for segment in ("constitution", "prompts", "templates", "architecture", "governance", "validation", "recommendations"):
                skill_content = skill_content.replace(f"`{segment}/", f"`{profile_prefix}/{segment}/")
            skill_content = re.sub(
                r"`(_[a-zA-Z][a-zA-Z0-9._-]+\.json)`",
                lambda m: f"`{profile_prefix}/{m.group(1)}`",
                skill_content,
            )
            skill_src.write_text(skill_content)

            # For Claude: also install as on-demand sub-agent in .claude/agents/
            if ai_assistant == "claude":
                agents_dir = project_path / ".claude" / "agents"
                agents_dir.mkdir(parents=True, exist_ok=True)
                (agents_dir / f"{profile_id}.md").write_text(skill_content)

        # Record what actually landed on disk (not the catalog's possibly-stale idea of it) so
        # `pandawa profile status` has an accurate "installed" baseline to diff against.
        installed_version = None
        try:
            manifest_data = json.loads((profile_dest / "profile.json").read_text(encoding="utf-8"))
            installed_version = manifest_data.get("version")
        except (FileNotFoundError, json.JSONDecodeError, OSError):
            pass
        _write_profile_lock_entry(
            project_path, profile_id,
            version=installed_version,
            ref="local" if local_path is not None else "main",
            source=str(local_path) if local_path is not None else "gitlab",
        )

        if tracker:
            tracker.complete("profile-extract", f"{profile_id} ready")
    except Exception as e:
        if tracker:
            tracker.error("profile-extract", str(e))
        raise
    finally:
        if tracker:
            tracker.add("profile-cleanup", "Remove profile archive")
        if zip_path is not None and zip_path.exists():
            zip_path.unlink()
            if tracker:
                tracker.complete("profile-cleanup")
            elif verbose:
                console.print(f"Cleaned up: {zip_path.name}")
        elif tracker and zip_path is None:
            tracker.skip("profile-cleanup", "no archive (local source)")

    return project_path


def ensure_executable_scripts(project_path: Path, tracker: StepTracker | None = None) -> None:
    """Ensure POSIX .sh scripts under .pandawa/scripts (recursively) have execute bits (no-op on Windows)."""
    if os.name == "nt":
        return  # Windows: skip silently
    scripts_root = project_path / ".pandawa" / "scripts"
    if not scripts_root.is_dir():
        return
    failures: list[str] = []
    updated = 0
    for script in scripts_root.rglob("*.sh"):
        try:
            if script.is_symlink() or not script.is_file():
                continue
            try:
                with script.open("rb") as f:
                    if f.read(2) != b"#!":
                        continue
            except Exception:
                continue
            st = script.stat(); mode = st.st_mode
            if mode & 0o111:
                continue
            new_mode = mode
            if mode & 0o400: new_mode |= 0o100
            if mode & 0o040: new_mode |= 0o010
            if mode & 0o004: new_mode |= 0o001
            if not (new_mode & 0o100):
                new_mode |= 0o100
            os.chmod(script, new_mode)
            updated += 1
        except Exception as e:
            failures.append(f"{script.relative_to(scripts_root)}: {e}")
    if tracker:
        detail = f"{updated} updated" + (f", {len(failures)} failed" if failures else "")
        tracker.add("chmod", "Set script permissions recursively")
        (tracker.error if failures else tracker.complete)("chmod", detail)
    else:
        if updated:
            console.print(f"[cyan]Updated execute permissions on {updated} script(s) recursively[/cyan]")
        if failures:
            console.print("[yellow]Some scripts could not be updated:[/yellow]")
            for f in failures:
                console.print(f"  - {f}")

@app.command()
def init(
    project_name: str = typer.Argument(None, help="Name for your new project directory (optional if using --here, or use '.' for current directory)"),
    ai_assistant: str = typer.Option(None, "--ai", help="AI assistant to use: claude, gemini, copilot, cursor-agent, qwen, opencode, codex, windsurf, kilocode, auggie, codebuddy, amp, shai, q, bob, or qoder "),
    script_type: str = typer.Option(None, "--script", help="Script type to use: sh or ps"),
    ignore_agent_tools: bool = typer.Option(False, "--ignore-agent-tools", help="Skip checks for AI agent tools like Claude Code"),
    no_git: bool = typer.Option(False, "--no-git", help="Skip git repository initialization"),
    here: bool = typer.Option(False, "--here", help="Initialize project in the current directory instead of creating a new one"),
    force: bool = typer.Option(False, "--force", help="Force merge/overwrite when using --here (skip confirmation)"),
    skip_tls: bool = typer.Option(False, "--skip-tls", help="Skip SSL/TLS verification (not recommended)"),
    debug: bool = typer.Option(False, "--debug", help="Show verbose diagnostic output for network and extraction failures"),
    gitlab_token: str = typer.Option(None, "--gitlab-token", help="GitLab token to use for API requests (or set GL_TOKEN or GITLAB_TOKEN environment variable)"),
    no_marketplace: bool = typer.Option(False, "--no-marketplace", help="Skip registering the Pandawa plugin marketplace in the project (Claude only)"),
    marketplace_url: str = typer.Option(None, "--marketplace-url", help="Override the Pandawa marketplace git URL (or set PANDAWA_MARKETPLACE_URL)"),
    no_guardrails: bool = typer.Option(False, "--no-guardrails", help="Skip writing baseline deny-first permission guardrails to .claude/settings.json (Claude only)"),
    no_claude_md: bool = typer.Option(False, "--no-claude-md", help="Skip scaffolding a starter CLAUDE.md project-context file"),
    profile: str = typer.Option(None, "--profile", help=f"Domain profile to apply. Available (offline seed — run 'pandawa profile list' for the live catalog): {', '.join(_PROFILE_SEED.keys())}"),
    profile_path: str = typer.Option(None, "--profile-path", help="Local directory to use as profile source instead of downloading (for development/testing)"),
):
    """
    Initialize a new Pandawa project from the latest template.

    This command will:
    1. Check that required tools are installed (git is optional)
    2. Let you choose your AI assistant
    3. Download the appropriate template from GitLab
    4. Extract the template to a new project directory or current directory
    5. (Claude) Register the Pandawa plugin marketplace in .claude/settings.json,
       enable the baseline pandawa-core plugin, write deny-first guardrails, and install
       the governance guard (skip marketplace/guard with --no-marketplace)
    6. Initialize a fresh git repository (if not --no-git and no existing repo)
    7. Optionally set up AI assistant commands

    Examples:
        pandawa init my-project
        pandawa init my-project --ai claude
        pandawa init my-project --ai copilot --no-git
        pandawa init --ignore-agent-tools my-project
        pandawa init . --ai claude         # Initialize in current directory
        pandawa init .                     # Initialize in current directory (interactive AI selection)
        pandawa init --here --ai claude    # Alternative syntax for current directory
        pandawa init --here --ai codex
        pandawa init --here --ai codebuddy
        pandawa init --here
        pandawa init --here --force  # Skip confirmation when current directory not empty
    """

    show_banner()
    _timer = ProcessTimer("pandawa init")

    if project_name == ".":
        here = True
        project_name = None  # Clear project_name to use existing validation logic

    if here and project_name:
        console.print("[red]Error:[/red] Cannot specify both project name and --here flag")
        raise typer.Exit(1)

    if not here and not project_name:
        console.print("[red]Error:[/red] Must specify either a project name, use '.' for current directory, or use --here flag")
        raise typer.Exit(1)

    if here:
        project_name = Path.cwd().name
        project_path = Path.cwd()

        existing_items = list(project_path.iterdir())
        if existing_items:
            console.print(f"[yellow]Warning:[/yellow] Current directory is not empty ({len(existing_items)} items)")
            console.print("[yellow]Template files will be merged with existing content and may overwrite existing files[/yellow]")
            if force:
                console.print("[cyan]--force supplied: skipping confirmation and proceeding with merge[/cyan]")
            else:
                response = typer.confirm("Do you want to continue?")
                if not response:
                    console.print("[yellow]Operation cancelled[/yellow]")
                    raise typer.Exit(0)
    else:
        project_path = Path(project_name).resolve()
        if project_path.exists():
            error_panel = Panel(
                f"Directory '[cyan]{project_name}[/cyan]' already exists\n"
                "Please choose a different project name or remove the existing directory.",
                title="[red]Directory Conflict[/red]",
                border_style="red",
                padding=(1, 2)
            )
            console.print()
            console.print(error_panel)
            raise typer.Exit(1)

    current_dir = Path.cwd()

    setup_lines = [
        "[cyan]Pandawa Project Setup[/cyan]",
        "",
        f"{'Project':<15} [green]{project_path.name}[/green]",
        f"{'Working Path':<15} [dim]{current_dir}[/dim]",
    ]

    if not here:
        setup_lines.append(f"{'Target Path':<15} [dim]{project_path}[/dim]")

    console.print(Panel("\n".join(setup_lines), border_style="cyan", padding=(1, 2)))

    should_init_git = False
    if not no_git:
        should_init_git = check_tool("git")
        if not should_init_git:
            console.print("[yellow]Git not found - will skip repository initialization[/yellow]")

    if ai_assistant:
        if ai_assistant not in AGENT_CONFIG:
            console.print(f"[red]Error:[/red] Invalid AI assistant '{ai_assistant}'. Choose from: {', '.join(AGENT_CONFIG.keys())}")
            raise typer.Exit(1)
        selected_ai = ai_assistant
    elif sys.stdin.isatty():
        # Interactive: arrow-key menu defaulting to claude. Pandawa is Claude-centric — the
        # marketplace, governance, and guard wiring only activate for --ai claude.
        ai_choices = {key: config["name"] for key, config in AGENT_CONFIG.items()}
        selected_ai = select_with_arrows(
            ai_choices,
            "Choose your AI assistant (Enter for claude):",
            "claude"
        )
    else:
        # Non-interactive (CI / piped stdin): default to claude without prompting/hanging.
        selected_ai = "claude"

    if not ignore_agent_tools:
        agent_config = AGENT_CONFIG.get(selected_ai)
        if agent_config and agent_config["requires_cli"]:
            install_url = agent_config["install_url"]
            if not check_tool(selected_ai):
                error_panel = Panel(
                    f"[cyan]{selected_ai}[/cyan] not found\n"
                    f"Install from: [cyan]{install_url}[/cyan]\n"
                    f"{agent_config['name']} is required to continue with this project type.\n\n"
                    "Tip: Use [cyan]--ignore-agent-tools[/cyan] to skip this check",
                    title="[red]Agent Detection Error[/red]",
                    border_style="red",
                    padding=(1, 2)
                )
                console.print()
                console.print(error_panel)
                raise typer.Exit(1)

    if script_type:
        if script_type not in SCRIPT_TYPE_CHOICES:
            console.print(f"[red]Error:[/red] Invalid script type '{script_type}'. Choose from: {', '.join(SCRIPT_TYPE_CHOICES.keys())}")
            raise typer.Exit(1)
        selected_script = script_type
    else:
        default_script = "ps" if os.name == "nt" else "sh"

        if sys.stdin.isatty():
            selected_script = select_with_arrows(SCRIPT_TYPE_CHOICES, "Choose script type (or press Enter)", default_script)
        else:
            selected_script = default_script

    # Profile selection
    selected_profile: str | None = profile
    # Best-effort live refresh so a freshly-published profile is recognized — only when it
    # can actually matter (an explicit --profile to validate, or an interactive picker about
    # to be shown), to avoid an unnecessary network round trip otherwise.
    if selected_profile or sys.stdin.isatty():
        _auto_refresh_profile_catalog()
    profile_config = _effective_profile_config()

    # --profile-path is a fully explicit local source (e.g. a profile author testing a new
    # profile that hasn't merged to profiles.json yet) — nothing will be downloaded
    # from GitLab, so the catalog gate (which only protects the download step) doesn't apply.
    if selected_profile and selected_profile not in profile_config and not profile_path:
        # No confirm-and-proceed-anyway escape hatch here (unlike the old release-asset
        # mechanism): downloading now requires a `path` from the catalog, so an unknown
        # profile has nothing to fetch — "try anyway" would just hit a guaranteed failure
        # two steps later. --profile-path is the only way to proceed with an unknown id.
        console.print(f"[red]Error:[/red] Unknown profile '{selected_profile}'. Available: {', '.join(profile_config.keys())}")
        console.print("[dim]If this profile was just added, the cache may be stale — try[/dim] [cyan]pandawa profile refresh[/cyan][dim] first.[/dim]")
        console.print("[dim]Testing a profile that hasn't merged to pandawa-marketplace-tooling's profiles.json yet? Pass[/dim] [cyan]--profile-path <dir>[/cyan][dim] to skip this check.[/dim]")
        raise typer.Exit(1)

    if selected_profile is None and sys.stdin.isatty():
        _none_key = "none"
        profile_choices: dict[str, str] = {_none_key: "No profile — general purpose project"}
        profile_choices.update({
            key: f"{cfg['name']}  —  {cfg['description']}"
            for key, cfg in profile_config.items()
        })
        _selected = select_with_arrows(profile_choices, "Choose a domain profile (optional):", _none_key)
        selected_profile = None if _selected == _none_key else _selected

    console.print(f"[cyan]Selected AI assistant:[/cyan] {selected_ai}")
    console.print(f"[cyan]Selected script type:[/cyan] {selected_script}")
    if selected_profile:
        _profile_name = profile_config.get(selected_profile, {}).get("name", selected_profile)
        console.print(f"[cyan]Selected profile:[/cyan] {selected_profile} ({_profile_name})")

    # Opsi 2: GitHub primary needs no token; only fetch GitLab token if user explicitly passed one (fallback)
    gitlab_token = _gitlab_token(gitlab_token)

    tracker = StepTracker("Initialize Pandawa Project")

    sys._pandawa_tracker_active = True

    tracker.add("precheck", "Check required tools")
    tracker.complete("precheck", "ok")
    tracker.add("ai-select", "Select AI assistant")
    tracker.complete("ai-select", f"{selected_ai}")
    tracker.add("script-select", "Select script type")
    tracker.complete("script-select", selected_script)
    tracker.add("profile-select", "Select domain profile")
    tracker.complete("profile-select", selected_profile if selected_profile else "none")
    for key, label in [
        ("fetch", "Fetch latest release"),
        ("download", "Download template"),
        ("extract", "Extract template"),
        ("zip-list", "Archive contents"),
        ("extracted-summary", "Extraction summary"),
        ("chmod", "Ensure scripts executable"),
        ("cleanup", "Cleanup"),
        ("marketplace", "Register plugin marketplace"),
        ("guardrails", "Write baseline guardrails"),
        ("governance", "Install governance guard"),
        ("context", "Scaffold CLAUDE.md"),
    ]:
        tracker.add(key, label)

    if selected_profile:
        for key, label in [
            ("profile-fetch", "Fetch profile from git"),
            ("profile-download", "Download profile"),
            ("profile-extract", "Extract profile"),
            ("profile-cleanup", "Cleanup profile"),
        ]:
            tracker.add(key, label)

    for key, label in [
        ("git", "Initialize git repository"),
        ("final", "Finalize"),
    ]:
        tracker.add(key, label)

    # Track git error message outside Live context so it persists
    git_error_message = None

    with Live(tracker.render(), console=console, refresh_per_second=8, transient=True) as live:
        tracker.attach_refresh(lambda: live.update(tracker.render()))
        try:
            verify = not skip_tls
            local_ssl_context = _get_ssl_context() if verify else False
            local_client = httpx.Client(verify=local_ssl_context)

            download_and_extract_template(project_path, selected_ai, selected_script, here, verbose=False, tracker=tracker, client=local_client, debug=debug, gitlab_token=gitlab_token)

            ensure_executable_scripts(project_path, tracker=tracker)

            # Skill registry + role agents (all hosts; native dir for supported ones).
            install_layers(project_path, selected_ai, tracker=tracker)

            # Point the project at the Pandawa plugin marketplace (Claude only).
            if selected_ai == "claude" and not no_marketplace:
                resolved_marketplace_url = marketplace_url or os.getenv("PANDAWA_MARKETPLACE_URL") or DEFAULT_MARKETPLACE_URL
                tracker.start("marketplace")
                configure_marketplace(project_path, url=resolved_marketplace_url, plugins=MARKETPLACE_BASELINE_PLUGINS, tracker=tracker)
            else:
                tracker.skip("marketplace", "Claude only" if selected_ai != "claude" else "--no-marketplace")

            # Baseline mechanical guardrails (deny-first, loose) — Claude only.
            if selected_ai == "claude" and not no_guardrails:
                tracker.start("guardrails")
                configure_guardrails(project_path, deny_rules=BASELINE_DENY_RULES, tracker=tracker)
            else:
                tracker.skip("guardrails", "Claude only" if selected_ai != "claude" else "--no-guardrails")

            # Governance guard: install the project-local hook + catalog that enforce
            # "one active governance plugin" (Claude only; needs the marketplace).
            if selected_ai == "claude" and not no_marketplace:
                tracker.start("governance")
                # Seed the catalog from the live marketplace first (best-effort; offline ->
                # built-in seed), then install the guard so the catalog reflects reality.
                try:
                    refresh_governance_catalog(project_path, url=resolved_marketplace_url,
                                               cli_token=gitlab_token, client=local_client)
                except Exception:
                    pass
                configure_governance_guard(project_path, tracker=tracker)
            else:
                tracker.skip("governance", "Claude only" if selected_ai != "claude" else "--no-marketplace")

            # Starter project-context file (CLAUDE.md) for agents.
            if not no_claude_md:
                scaffold_project_context(project_path, tracker=tracker)
            else:
                tracker.skip("context", "--no-claude-md")

            # Domain profile
            if selected_profile:
                if profile_path:
                    local_profile_path = Path(profile_path).resolve()
                else:
                    local_profile_path = _get_profile_local_path(selected_profile)
                download_and_extract_profile(project_path, selected_profile, selected_ai, local_path=local_profile_path, verbose=False, tracker=tracker, client=local_client, debug=debug, gitlab_token=gitlab_token)
            else:
                tracker.skip("profile-fetch", "no profile selected")
                tracker.skip("profile-download", "no profile selected")
                tracker.skip("profile-extract", "no profile selected")
                tracker.skip("profile-cleanup", "no profile selected")

            if not no_git:
                tracker.start("git")
                if is_git_repo(project_path):
                    tracker.complete("git", "existing repo detected")
                elif should_init_git:
                    success, error_msg = init_git_repo(project_path, quiet=True)
                    if success:
                        tracker.complete("git", "initialized")
                    else:
                        tracker.error("git", "init failed")
                        git_error_message = error_msg
                else:
                    tracker.skip("git", "git not available")
            else:
                tracker.skip("git", "--no-git flag")

            tracker.complete("final", "project ready")
        except Exception as e:
            tracker.error("final", str(e))
            console.print(Panel(f"Initialization failed: {e}", title="Failure", border_style="red"))
            if debug:
                _env_pairs = [
                    ("Python", sys.version.split()[0]),
                    ("Platform", sys.platform),
                    ("CWD", str(Path.cwd())),
                ]
                _label_width = max(len(k) for k, _ in _env_pairs)
                env_lines = [f"{k.ljust(_label_width)} → [bright_black]{v}[/bright_black]" for k, v in _env_pairs]
                console.print(Panel("\n".join(env_lines), title="Debug Environment", border_style="magenta"))
            _timer.stop(status="failed", error=str(e))
            show_audit_panel(_timer, agent=selected_ai, script_type=selected_script,
                             profile=selected_profile, project_path=None, tracker=tracker)
            if not here and project_path.exists():
                shutil.rmtree(project_path)
            raise typer.Exit(1)
        finally:
            pass

    console.print(tracker.render())
    console.print("\n[bold green]Project ready.[/bold green]")
    
    # Show git error details if initialization failed
    if git_error_message:
        console.print()
        git_error_panel = Panel(
            f"[yellow]Warning:[/yellow] Git repository initialization failed\n\n"
            f"{git_error_message}\n\n"
            f"[dim]You can initialize git manually later with:[/dim]\n"
            f"[cyan]cd {project_path if not here else '.'}[/cyan]\n"
            f"[cyan]git init[/cyan]\n"
            f"[cyan]git add .[/cyan]\n"
            f"[cyan]git commit -m \"Initial commit\"[/cyan]",
            title="[red]Git Initialization Failed[/red]",
            border_style="red",
            padding=(1, 2)
        )
        console.print(git_error_panel)

    # Agent folder security notice
    agent_config = AGENT_CONFIG.get(selected_ai)
    if agent_config:
        agent_folder = agent_config["folder"]
        security_notice = Panel(
            f"Some agents may store credentials, auth tokens, or other identifying and private artifacts in the agent folder within your project.\n"
            f"Consider adding [cyan]{agent_folder}[/cyan] (or parts of it) to [cyan].gitignore[/cyan] to prevent accidental credential leakage.",
            title="[yellow]Agent Folder Security[/yellow]",
            border_style="yellow",
            padding=(1, 2)
        )
        console.print()
        console.print(security_notice)

    steps_lines = []
    if not here:
        steps_lines.append(f"1. Go to the project folder: [cyan]cd {project_name}[/cyan]")
        step_num = 2
    else:
        steps_lines.append("1. You're already in the project directory!")
        step_num = 2

    # Add Codex-specific setup step if needed
    if selected_ai == "codex":
        codex_path = project_path / ".codex"
        quoted_path = shlex.quote(str(codex_path))
        if os.name == "nt":  # Windows
            cmd = f"setx CODEX_HOME {quoted_path}"
        else:  # Unix-like systems
            cmd = f"export CODEX_HOME={quoted_path}"
        
        steps_lines.append(f"{step_num}. Set [cyan]CODEX_HOME[/cyan] environment variable before running Codex: [cyan]{cmd}[/cyan]")
        step_num += 1

    steps_lines.append(f"{step_num}. Start using slash commands with your AI agent:")

    steps_lines.append("   [cyan]/pandawa[/] - Guided entry point (any agent): run with no arguments for a menu, or describe your goal and it routes to the right command/agent/skill")
    steps_lines.append("   2.1 [cyan]/pandawa.constitution[/] - Establish project principles")
    steps_lines.append("   2.2 [cyan]/pandawa.specify[/] - Create baseline specification")
    steps_lines.append("   2.3 [cyan]/pandawa.plan[/] - Create implementation plan")
    steps_lines.append("   2.4 [cyan]/pandawa.tasks[/] - Generate actionable tasks")
    steps_lines.append("   2.5 [cyan]/pandawa.implement[/] - Execute implementation")

    if selected_ai == "claude" and not no_marketplace:
        steps_lines.append("")
        steps_lines.append(f"[bold]Plugins (skills & agents):[/] marketplace [cyan]{MARKETPLACE_NAME}[/] is registered and [cyan]pandawa-core[/] enabled — trust the folder in Claude Code to activate. Add packs as needed:")
        steps_lines.append("   [cyan]/plugin install tmf-oda-constitution@pandawa[/]   - TM Forum ODA constitution/governance framework")
        steps_lines.append("   [cyan]/plugin install docs-pack@pandawa[/]  - docx / pdf / pptx / xlsx")
        steps_lines.append("")
        steps_lines.append("[bold]Governance packs[/] are mutually exclusive (only one active). Switch with [cyan]pandawa governance use <name>[/]; check with [cyan]pandawa governance status[/]. Restart Claude Code after switching.")
        steps_lines.append("")
        steps_lines.append("[bold]Project setup:[/] baseline deny-first guardrails written to [cyan].claude/settings.json[/]; fill in [cyan]CLAUDE.md[/] with project context for better agent results.")

    steps_panel = Panel("\n".join(steps_lines), title="Next Steps", border_style="cyan", padding=(1,2))
    console.print()
    console.print(steps_panel)

    enhancement_lines = [
        "Optional commands that you can use for your specs [bright_black](improve quality & confidence)[/bright_black]",
        "",
        f"○ [cyan]/pandawa.clarify[/] [bright_black](optional)[/bright_black] - Ask structured questions to de-risk ambiguous areas before planning (run before [cyan]/pandawa.plan[/] if used)",
        f"○ [cyan]/pandawa.analyze[/] [bright_black](optional)[/bright_black] - Cross-artifact consistency & alignment report (after [cyan]/pandawa.tasks[/], before [cyan]/pandawa.implement[/])",
        f"○ [cyan]/pandawa.checklist[/] [bright_black](optional)[/bright_black] - Generate quality checklists to validate requirements completeness, clarity, and consistency (after [cyan]/pandawa.plan[/])",
        f"○ [cyan]/pandawa.test[/] [bright_black](optional)[/bright_black] - Generate missing unit tests and run SonarQube-style code quality compliance checks",
        f"○ [cyan]/pandawa.redesign[/] [bright_black](optional)[/bright_black] - Incrementally rework one part of an implemented feature (scoped edits with checkpoint & rollback)"
    ]
    enhancements_panel = Panel("\n".join(enhancement_lines), title="Enhancement Commands", border_style="cyan", padding=(1,2))
    console.print()
    console.print(enhancements_panel)

    if selected_profile:
        profile_cfg = _effective_profile_config().get(
            selected_profile, {"name": selected_profile, "description": ""}
        )
        profile_lines = [
            f"[bold]{profile_cfg['name']}[/bold] — {profile_cfg['description']}",
            "",
            f"Location: [cyan].pandawa/profiles/{selected_profile}/[/cyan]",
        ]
        if profile_path:
            profile_lines.append(f"Source: [dim]local ({profile_path})[/dim]")
        if selected_ai == "claude":
            profile_lines.append(f"Claude agent: [cyan].claude/agents/{selected_profile}.md[/cyan]")
        profile_panel = Panel("\n".join(profile_lines), title="[green]Domain Profile Installed[/green]", border_style="green", padding=(1, 2))
        console.print()
        console.print(profile_panel)

    _timer.stop()
    show_audit_panel(_timer, agent=selected_ai, script_type=selected_script,
                     profile=selected_profile, project_path=project_path, tracker=tracker)

@app.command()
def check():
    """Check that all required tools are installed."""
    show_banner()
    _timer = ProcessTimer("pandawa check")
    console.print("[bold]Checking for installed tools...[/bold]\n")

    tracker = StepTracker("Check Available Tools")

    tracker.add("git", "Git version control")
    git_ok = check_tool("git", tracker=tracker)

    agent_results = {}
    for agent_key, agent_config in AGENT_CONFIG.items():
        agent_name = agent_config["name"]
        requires_cli = agent_config["requires_cli"]

        tracker.add(agent_key, agent_name)

        if requires_cli:
            agent_results[agent_key] = check_tool(agent_key, tracker=tracker)
        else:
            # IDE-based agent - skip CLI check and mark as optional
            tracker.skip(agent_key, "IDE-based, no CLI check")
            agent_results[agent_key] = False  # Don't count IDE agents as "found"

    # Check VS Code variants (not in agent config)
    tracker.add("code", "Visual Studio Code")
    code_ok = check_tool("code", tracker=tracker)

    tracker.add("code-insiders", "Visual Studio Code Insiders")
    code_insiders_ok = check_tool("code-insiders", tracker=tracker)

    console.print(tracker.render())

    console.print("\n[bold green]Pandawa CLI is ready to use![/bold green]")

    if not git_ok:
        console.print("[dim]Tip: Install git for repository management[/dim]")

    if not any(agent_results.values()):
        console.print("[dim]Tip: Install an AI assistant for the best experience[/dim]")

    _timer.stop()
    show_audit_panel(_timer, tracker=tracker)

@app.command()
def version(
    gitlab_token: str = typer.Option(None, "--gitlab-token", help="GitLab token (or set GL_TOKEN / GITLAB_TOKEN env var)"),
):
    """Display version and system information."""
    import platform
    import importlib.metadata
    
    show_banner()
    
    # Get CLI version from package metadata
    cli_version = "unknown"
    try:
        cli_version = importlib.metadata.version("pandawa-cli")
    except Exception:
        # Fallback: try reading from pyproject.toml if running from source
        try:
            import tomllib
            pyproject_path = Path(__file__).parent.parent.parent / "pyproject.toml"
            if pyproject_path.exists():
                with open(pyproject_path, "rb") as f:
                    data = tomllib.load(f)
                    cli_version = data.get("project", {}).get("version", "unknown")
        except Exception:
            pass
    
    gitlab_token = _gitlab_token(gitlab_token)

    # Opsi 2: fetch version from GitHub first, fallback GitLab
    api_url = f"https://api.github.com/repos/{DEFAULT_GITHUB_REPO}/releases/latest"
    gh_headers = {"Accept": "application/vnd.github.v3+json"}
    gh_tok = os.getenv("GITHUB_TOKEN") or os.getenv("GH_TOKEN")
    if gh_tok:
        gh_headers["Authorization"] = f"Bearer {gh_tok.strip()}"

    template_version = "unknown"
    release_date = "unknown"

    try:
        response = _get_client().get(
            api_url,
            timeout=10,
            follow_redirects=True,
            headers=gh_headers,
        )
        if response.status_code == 200:
            data = response.json()
            # GitHub returns dict, GitLab returns list — handle both
            if isinstance(data, dict):
                release_data = data
            elif isinstance(data, list) and data:
                release_data = data[0]
            else:
                release_data = None
            if release_data:
                template_version = release_data.get("tag_name", "unknown")
                if template_version.startswith("v"):
                    template_version = template_version[1:]
                release_date = release_data.get("released_at") or release_data.get("published_at", "unknown")
                if release_date != "unknown":
                    try:
                        dt = datetime.fromisoformat(release_date.replace('Z', '+00:00'))
                        release_date = dt.strftime("%Y-%m-%d")
                    except Exception:
                        pass
        # fallback to GitLab if GitHub failed (e.g., no release yet)
        if template_version == "unknown":
            try:
                gl_api = "https://git.neuron.id/api/v4/projects/research%2Fpandawa/releases?per_page=1"
                gl_resp = _get_client().get(gl_api, timeout=10, follow_redirects=True, headers=_gitlab_auth_headers(gitlab_token))
                if gl_resp.status_code == 200:
                    gl_data = gl_resp.json()
                    if isinstance(gl_data, list) and gl_data:
                        rd = gl_data[0]
                        tv = rd.get("tag_name","unknown")
                        if tv.startswith("v"): tv=tv[1:]
                        template_version = tv
                        rd2 = rd.get("released_at","unknown")
                        if rd2 != "unknown":
                            try:
                                dt = datetime.fromisoformat(rd2.replace('Z','+00:00'))
                                release_date = dt.strftime("%Y-%m-%d")
                            except: pass
            except Exception:
                pass
    except Exception:
        pass

    info_table = Table(show_header=False, box=None, padding=(0, 2))
    info_table.add_column("Key", style="cyan", justify="right")
    info_table.add_column("Value", style="white")

    info_table.add_row("CLI Version", cli_version)
    info_table.add_row("Template Version", template_version)
    info_table.add_row("Released", release_date)
    info_table.add_row("", "")
    info_table.add_row("Python", platform.python_version())
    info_table.add_row("Platform", platform.system())
    info_table.add_row("Architecture", platform.machine())
    info_table.add_row("OS Version", platform.version())

    panel = Panel(
        info_table,
        title="[bold cyan]Pandawa CLI Information[/bold cyan]",
        border_style="cyan",
        padding=(1, 2)
    )

    console.print(panel)
    console.print()

# ---- `pandawa usage` command ---------------------------------------------------------------

# Sonnet 4.x pricing (USD per 1M tokens) — used for cost estimates.
# Cache read is 10% of input price; cache write is 125% of input price.
_MODEL_PRICING: dict[str, dict[str, float]] = {
    "claude-sonnet-4-6": {"input": 3.00, "output": 15.00},
    "claude-sonnet-4-5": {"input": 3.00, "output": 15.00},
    "claude-opus-4-8":   {"input": 15.00, "output": 75.00},
    "claude-haiku-4-5":  {"input": 0.80,  "output": 4.00},
}
_DEFAULT_PRICING = {"input": 3.00, "output": 15.00}


def _estimate_cost(input_tok: int, output_tok: int, cache_read: int, cache_write: int, model: str) -> float:
    """Estimate USD cost from token counts using published Anthropic pricing."""
    p = _MODEL_PRICING.get(model) or _MODEL_PRICING.get(re.sub(r"-\d{8}$", "", model)) or _DEFAULT_PRICING
    inp_price   = p["input"]   / 1_000_000
    out_price   = p["output"]  / 1_000_000
    cr_price    = inp_price * 0.10   # cache read = 10% of input
    cw_price    = inp_price * 1.25   # cache write = 125% of input
    return (input_tok * inp_price + output_tok * out_price
            + cache_read * cr_price + cache_write * cw_price)


def _fmt_duration(seconds: float) -> str:
    if seconds < 60:
        return f"{seconds:.0f}s"
    m, s = divmod(int(seconds), 60)
    return f"{m}m {s}s"


def _fmt_local_time(ts: "str | None") -> str:
    """ISO UTC timestamp -> local 'HH:MM:SS', or '—' if unparseable/missing."""
    if not ts:
        return "—"
    try:
        return datetime.fromisoformat(ts.replace("Z", "+00:00")).astimezone().strftime("%H:%M:%S")
    except Exception:
        return "—"


def _claude_sessions_dir(cwd: "Path | None" = None) -> "tuple[Path, str] | None":
    """Return (sessions_dir, match_type) for the given cwd, or None if not found.

    match_type is one of: 'exact', 'suffix', 'name'.

    Resolution order (stops at first hit):
    1. Exact key match: full path → key (e.g. -Users-alice-projects-foo)
    2. Suffix match: any project dir whose key ends with the same trailing
       segments (handles username differences between machines, e.g. the key
       ends in -projects-foo on both machines even though the prefix differs)
    3. Name match: any project dir whose last segment equals the project name
       (e.g. -foo). Picks the most recently modified one when multiple match.
    """
    projects_root = Path.home() / ".claude" / "projects"
    if not projects_root.is_dir():
        return None

    target = Path(cwd).resolve() if cwd else Path.cwd()

    # 1. Exact match — Claude Code key: path separators, colons, underscores → hyphens
    key = str(target).replace("\\", "-").replace("/", "-").replace(":", "-").replace("_", "-")
    d = projects_root / key
    if d.is_dir():
        return (d, "exact")

    # Build list of all candidate dirs once
    candidates = [p for p in projects_root.iterdir() if p.is_dir()]

    def _norm(s: str) -> str:
        # Claude Code normalizes path segments: backslash, colon, underscore → hyphen
        return s.replace("\\", "-").replace(":", "-").replace("_", "-")

    # 2. Suffix match — try progressively shorter trailing segments of target
    #    until we find a unique hit (at least 2 parts to avoid false positives)
    parts = target.parts  # e.g. ('/', 'Users', 'alice', 'projects', 'foo')
    for depth in range(len(parts) - 1, 1, -1):
        suffix = _norm("-".join(parts[-depth:]))  # normalize separators + underscores
        matches = [p for p in candidates if p.name.endswith(f"-{suffix}") or p.name == suffix]
        if len(matches) == 1:
            return (matches[0], "suffix")
        if len(matches) > 1:
            # Multiple hits at this depth — don't guess, try shorter suffix
            continue

    # 3. Name-only match — just the project directory name
    name = _norm(target.name)
    name_matches = [p for p in candidates if p.name.endswith(f"-{name}") or p.name == name]
    if name_matches:
        best = max(name_matches, key=lambda p: p.stat().st_mtime)
        return (best, "name")

    return None


def _parse_session_commands(path: Path) -> list[dict]:
    """Parse a session JSONL and return per-/pandawa.* command stats (sorted by start time).

    Strategy: walk entries in timestamp order; each user turn containing
    <command-name>/pandawa.*</command-name> opens a new command block. All
    subsequent assistant turns (with usage) are attributed to that block until
    the next command turn or end of file.
    """
    entries: list[dict] = []
    try:
        with open(path, encoding="utf-8") as f:
            for raw in f:
                raw = raw.strip()
                if not raw:
                    continue
                try:
                    entries.append(json.loads(raw))
                except json.JSONDecodeError:
                    continue
    except Exception:
        return []

    entries.sort(key=lambda e: e.get("timestamp") or "")

    blocks: list[dict] = []
    cur: "dict | None" = None

    for entry in entries:
        t = entry.get("type")
        ts = entry.get("timestamp") or ""

        if t == "user":
            content = str(entry.get("message", {}).get("content", ""))
            m = re.search(r"<command-name>(/pandawa\.[^<]+)</command-name>", content)
            if m:
                if cur:
                    blocks.append(cur)
                cur = {
                    "command": m.group(1).strip(),
                    "start_ts": ts,
                    "end_ts": ts,
                    "turns": 0,
                    "input_tokens": 0,
                    "output_tokens": 0,
                    "cache_read": 0,
                    "cache_write": 0,
                    "models": set(),
                }
                continue

        if t == "assistant" and cur:
            msg = entry.get("message", {})
            u = msg.get("usage", {})
            if u:
                cur["turns"] += 1
                cur["input_tokens"]  += u.get("input_tokens", 0)
                cur["output_tokens"] += u.get("output_tokens", 0)
                cur["cache_read"]    += u.get("cache_read_input_tokens", 0)
                cur["cache_write"]   += u.get("cache_creation_input_tokens", 0)
                if ts:
                    cur["end_ts"] = ts
                model = msg.get("model")
                if model:
                    cur["models"].add(model)

    if cur:
        blocks.append(cur)

    # Compute derived fields
    for b in blocks:
        try:
            s = datetime.fromisoformat(b["start_ts"].replace("Z", "+00:00"))
            e = datetime.fromisoformat(b["end_ts"].replace("Z", "+00:00"))
            b["duration_s"] = max(0.0, (e - s).total_seconds())
        except Exception:
            b["duration_s"] = 0.0
        primary_model = next(iter(sorted(b["models"])), "")
        b["cost_usd"] = _estimate_cost(
            b["input_tokens"], b["output_tokens"],
            b["cache_read"], b["cache_write"], primary_model,
        )
        b["date"] = (b["start_ts"] or "")[:10]

    return blocks


def _parse_session_file(path: Path) -> dict:
    """Aggregate token usage from a single session .jsonl file."""
    stats: dict = {
        "session_id": path.stem,
        "title": None,
        "date": None,
        "turns": 0,
        "input_tokens": 0,
        "output_tokens": 0,
        "cache_read": 0,
        "cache_write": 0,
        "models": set(),
    }
    try:
        with open(path, encoding="utf-8") as f:
            for raw in f:
                raw = raw.strip()
                if not raw:
                    continue
                try:
                    entry = json.loads(raw)
                except json.JSONDecodeError:
                    continue
                t = entry.get("type")
                ts = entry.get("timestamp", "")
                if ts and not stats["date"]:
                    stats["date"] = ts[:10]
                if t == "ai-title":
                    stats["title"] = entry.get("aiTitle")
                if t == "assistant":
                    msg = entry.get("message", {})
                    u = msg.get("usage", {})
                    if u:
                        stats["turns"] += 1
                        stats["input_tokens"] += u.get("input_tokens", 0)
                        stats["output_tokens"] += u.get("output_tokens", 0)
                        stats["cache_read"] += u.get("cache_read_input_tokens", 0)
                        stats["cache_write"] += u.get("cache_creation_input_tokens", 0)
                        model = msg.get("model")
                        if model:
                            stats["models"].add(model)
    except Exception:
        pass
    return stats


_TASK_CHECKBOX_RE = re.compile(r"^\s*[-*]\s*\[( |x|X)\]")


def _scan_delivery_tasks(project_path: Path) -> list[dict]:
    """Scan specs/**/tasks.md (plus a root tasks.md) for task completion.

    Returns one dict per tasks.md with completed/total task counts, used to
    compute the AI-DLC 'predictability rate' (commitments delivered vs. made).
    """
    results: list[dict] = []
    candidates: list[Path] = []
    specs_dir = project_path / "specs"
    if specs_dir.is_dir():
        candidates.extend(sorted(specs_dir.glob("*/tasks.md")))
    root_tasks = project_path / "tasks.md"
    if root_tasks.is_file():
        candidates.append(root_tasks)

    for tf in candidates:
        total = done = 0
        try:
            for line in tf.read_text(encoding="utf-8").splitlines():
                m = _TASK_CHECKBOX_RE.match(line)
                if not m:
                    continue
                total += 1
                if m.group(1) in ("x", "X"):
                    done += 1
        except Exception:
            continue
        if total == 0:
            continue
        try:
            feature = tf.parent.name if tf.parent != project_path else "(root)"
        except Exception:
            feature = tf.parent.name
        results.append({
            "feature": feature,
            "path": tf,
            "total": total,
            "done": done,
            "pct": (done / total * 100.0) if total else 0.0,
        })
    return results


def _usage_delivery(project_path: Path, result) -> None:
    """Render AI-DLC-style delivery metrics for a project.

    Predictability rate comes from tasks.md completion (commitments delivered vs.
    made). Cycle time and phase mix come from /pandawa.* session history when present.
    Metrics that need a baseline or per-run bug data are reported honestly as such,
    rather than fabricated — LOC / acceptance-rate style numbers are deliberately omitted.
    """
    def _fmt_tok(n: int) -> str:
        if n >= 1_000_000:
            return f"{n/1_000_000:.1f}M"
        if n >= 1_000:
            return f"{n/1_000:.1f}K"
        return str(n)

    console.print()
    console.print(Panel(
        f"[dim]Project  [/dim] [cyan]{project_path}[/cyan]",
        title="[bold]Pandawa — Delivery Metrics (AI-DLC style)[/bold]",
        border_style="cyan",
        padding=(1, 2),
    ))

    # ---- 1. Predictability rate (tasks delivered vs. planned) ----
    tasks_scan = _scan_delivery_tasks(project_path)
    console.print("[bold cyan]Predictability[/bold cyan] [dim]— tasks completed vs. planned in tasks.md (AI-DLC target: >80%)[/dim]")
    if not tasks_scan:
        console.print("  [yellow]No tasks.md found[/yellow] under specs/*/ or repo root — run [cyan]/pandawa.tasks[/cyan] first.\n")
    else:
        ptbl = Table(show_header=True, header_style="bold cyan", box=None, padding=(0, 1), show_edge=False)
        ptbl.add_column("Feature", style="cyan", min_width=18)
        ptbl.add_column("Done",    justify="right", min_width=5, no_wrap=True)
        ptbl.add_column("Total",   justify="right", min_width=5, no_wrap=True)
        ptbl.add_column("Predictability", justify="right", min_width=13, no_wrap=True)
        tot_done = sum(t["done"] for t in tasks_scan)
        tot_total = sum(t["total"] for t in tasks_scan)
        for t in tasks_scan:
            pct = t["pct"]
            color = "green" if pct >= 80 else ("yellow" if pct >= 50 else "red")
            ptbl.add_row(t["feature"], str(t["done"]), str(t["total"]), f"[{color}]{pct:.0f}%[/{color}]")
        overall = (tot_done / tot_total * 100.0) if tot_total else 0.0
        ocolor = "green" if overall >= 80 else ("yellow" if overall >= 50 else "red")
        ptbl.add_section()
        ptbl.add_row("[bold]OVERALL[/bold]", f"[bold]{tot_done}[/bold]", f"[bold]{tot_total}[/bold]",
                     f"[bold {ocolor}]{overall:.0f}%[/bold {ocolor}]")
        console.print(ptbl)
        console.print()

    # ---- 2. Cycle time & phase mix (from session history, if any) ----
    blocks: list[dict] = []
    if result is not None:
        sessions_dir, _ = result
        for f in sorted(sessions_dir.glob("*.jsonl")):
            blocks.extend(_parse_session_commands(f))

    if not blocks:
        console.print("[bold cyan]Cycle time & phase mix[/bold cyan]")
        console.print("  [dim]No /pandawa.* command history yet — run commands inside Claude Code to populate this.[/dim]\n")
    else:
        starts, ends = [], []
        for b in blocks:
            try:
                starts.append(datetime.fromisoformat((b.get("start_ts") or "").replace("Z", "+00:00")))
                ends.append(datetime.fromisoformat((b.get("end_ts") or "").replace("Z", "+00:00")))
            except Exception:
                continue
        console.print("[bold cyan]Cycle time[/bold cyan] [dim]— wall-clock across all /pandawa.* runs (first command → last)[/dim]")
        if starts and ends:
            span = max(ends) - min(starts)
            active = sum(b.get("duration_s", 0.0) for b in blocks)
            console.print(f"  End-to-end span : [bold]{_fmt_duration(span.total_seconds())}[/bold]  "
                          f"[dim]({_fmt_local_time(min(starts).isoformat())} → {_fmt_local_time(max(ends).isoformat())})[/dim]")
            console.print(f"  Active AI time  : [bold]{_fmt_duration(active)}[/bold]  [dim](sum of per-command durations)[/dim]")
        console.print()

        # phase mix
        phase_agg: dict[str, dict] = {}
        for b in blocks:
            key = b["command"]
            a = phase_agg.setdefault(key, {"runs": 0, "output": 0, "cost": 0.0, "dur": 0.0})
            a["runs"] += 1
            a["output"] += b.get("output_tokens", 0)
            a["cost"] += b.get("cost_usd", 0.0)
            a["dur"] += b.get("duration_s", 0.0)
        console.print("[bold cyan]Phase mix[/bold cyan] [dim]— where time and tokens went, per command[/dim]")
        mtbl = Table(show_header=True, header_style="bold cyan", box=None, padding=(0, 1), show_edge=False)
        mtbl.add_column("Command", style="cyan", min_width=18)
        mtbl.add_column("Runs",   justify="right", style="dim", min_width=4, no_wrap=True)
        mtbl.add_column("Duration", justify="right", min_width=8, no_wrap=True)
        mtbl.add_column("Output", justify="right", min_width=6, no_wrap=True)
        mtbl.add_column("Cost (USD)", justify="right", style="yellow", min_width=9, no_wrap=True)
        t_runs = t_out = 0
        t_cost = t_dur = 0.0
        for cmd in sorted(phase_agg, key=lambda k: phase_agg[k]["cost"], reverse=True):
            a = phase_agg[cmd]
            mtbl.add_row(cmd, str(a["runs"]), _fmt_duration(a["dur"]), _fmt_tok(a["output"]), f"${a['cost']:.4f}")
            t_runs += a["runs"]; t_out += a["output"]; t_cost += a["cost"]; t_dur += a["dur"]
        mtbl.add_section()
        mtbl.add_row("[bold]TOTAL[/bold]", f"[bold]{t_runs}[/bold]", f"[bold]{_fmt_duration(t_dur)}[/bold]",
                     f"[bold cyan]{_fmt_tok(t_out)}[/bold cyan]", f"[bold yellow]${t_cost:.4f}[/bold yellow]")
        console.print(mtbl)
        console.print()

    # ---- 3. Honest notes on what these numbers can and can't say ----
    console.print("[bold cyan]Notes[/bold cyan]")
    console.print(
        "  [dim]• Predictability = tasks marked [X] in tasks.md ÷ total tasks. Mark tasks done as you go "
        "(/pandawa.implement does this) to keep it meaningful.[/dim]\n"
        "  [dim]• Velocity improvement (vs. non-AI) and defect-rate-normalized-to-velocity need an A/B "
        "baseline this tool doesn't have — measure those with a same-work comparison, not from this data.[/dim]\n"
        "  [dim]• Defect signal: run [cyan]/pandawa.test[/cyan] for Bug Reports and [cyan]/pandawa.operate[/cyan] "
        "for production anomalies; those live in their run output, not in this summary.[/dim]"
    )


@app.command()
def usage(
    limit: int = typer.Option(10, "--limit", "-n", help="Number of recent sessions to display (0 = all)."),
    cwd: str = typer.Option(None, "--cwd", help="Project directory to read sessions for (default: current directory)."),
    commands: bool = typer.Option(False, "--commands", "-c", help="Show per-/pandawa.* command breakdown with cost and duration."),
    delivery: bool = typer.Option(False, "--delivery", "-d", help="Show AI-DLC-style delivery metrics: predictability rate, cycle time, and phase mix."),
):
    """Show Claude Code token usage for this project from session history.

    Reads ~/.claude/projects/<key>/*.jsonl and aggregates input/output/cache
    tokens, turn count, and model per session. Useful after running /pandawa.*
    skills directly inside Claude Code.

    Use --commands to see a per-command breakdown with cost estimates and duration.
    """
    project_path = Path(cwd).resolve() if cwd else Path.cwd()
    result = _claude_sessions_dir(project_path)

    # ---- delivery-metrics mode (works even without session history) ----
    if delivery:
        _usage_delivery(project_path, result)
        return

    if result is None:
        projects_root = Path.home() / ".claude" / "projects"
        console.print(f"[yellow]No Claude Code session history found[/yellow] for [cyan]{project_path}[/cyan].")
        if projects_root.is_dir():
            known = sorted(p.name for p in projects_root.iterdir() if p.is_dir())
            if known:
                console.print(f"\n[dim]Known project caches in {projects_root}:[/dim]")
                for k in known:
                    console.print(f"  [bright_black]{k}[/bright_black]")
                console.print("\n[dim]Use [cyan]--cwd <path>[/cyan] to point to the matching project directory.[/dim]")
        else:
            console.print("[dim]Run some /pandawa.* commands inside Claude Code first, then re-run this.[/dim]")
        raise typer.Exit(0)

    sessions_dir, match_type = result

    if match_type != "exact":
        console.print(
            f"[yellow]Note:[/yellow] No exact session cache found for [cyan]{project_path}[/cyan].\n"
            f"[dim]Using closest match ({match_type}): {sessions_dir}[/dim]\n"
        )

    jsonl_files = sorted(sessions_dir.glob("*.jsonl"), key=lambda p: p.stat().st_mtime)
    if not jsonl_files:
        console.print(f"[yellow]No session files found[/yellow] in {sessions_dir}.")
        raise typer.Exit(0)

    def _fmt_tok(n: int) -> str:
        if n >= 1_000_000:
            return f"{n/1_000_000:.1f}M"
        if n >= 1_000:
            return f"{n/1_000:.1f}K"
        return str(n)

    # ---- per-command breakdown mode ----
    if commands:
        all_cmds: list[dict] = []
        for f in jsonl_files:
            all_cmds.extend(_parse_session_commands(f))

        all_cmds.sort(key=lambda c: c.get("start_ts") or "", reverse=True)
        shown_cmds = all_cmds if limit == 0 else all_cmds[:limit]

        console.print()
        console.print(Panel(
            f"[dim]Project  [/dim] [cyan]{project_path}[/cyan]\n"
            f"[dim]Sessions [/dim] [bright_black]{sessions_dir}[/bright_black]\n"
            f"[dim]Found    [/dim] {len(all_cmds)} /pandawa.* command run(s)"
            + (f"  [dim](showing latest {len(shown_cmds)})[/dim]" if limit and len(all_cmds) > limit else ""),
            title="[bold]Claude Code — Per-Command Usage[/bold]",
            border_style="cyan",
            padding=(1, 2),
        ))

        if not shown_cmds:
            console.print("[yellow]No /pandawa.* commands found in session history.[/yellow]")
            console.print("[dim]Run a /pandawa.* command inside Claude Code, then re-run this.[/dim]")
            raise typer.Exit(0)

        ctbl = Table(show_header=True, header_style="bold cyan", box=None, padding=(0, 1), show_edge=False)
        ctbl.add_column("Date",     style="bright_black", min_width=10, no_wrap=True)
        ctbl.add_column("Command",  style="cyan",         min_width=18, no_wrap=True)
        ctbl.add_column("Start",    style="bright_black", justify="right", min_width=8,  no_wrap=True)
        ctbl.add_column("End",      style="bright_black", justify="right", min_width=8,  no_wrap=True)
        ctbl.add_column("Duration", justify="right",      min_width=8,  no_wrap=True)
        ctbl.add_column("Turns",    justify="right", style="dim", min_width=5, no_wrap=True)
        ctbl.add_column("Output",   justify="right",      min_width=6,  no_wrap=True)
        ctbl.add_column("Cache hit",justify="right", style="green", min_width=9, no_wrap=True)
        ctbl.add_column("Cost (USD)",justify="right", style="yellow", min_width=9, no_wrap=True)
        ctbl.add_column("Model",    style="dim",          min_width=10, no_wrap=True)

        total_cost = total_out = total_cache_r = total_dur = total_turns_c = 0.0
        for b in shown_cmds:
            short_models = sorted(
                re.sub(r"-\d{8}$", "", m.replace("claude-", "")) for m in b["models"]
            )
            model_str = " / ".join(short_models) if short_models else "—"
            ctbl.add_row(
                b["date"] or "—",
                b["command"],
                _fmt_local_time(b.get("start_ts")),
                _fmt_local_time(b.get("end_ts")),
                _fmt_duration(b["duration_s"]),
                str(b["turns"]),
                _fmt_tok(b["output_tokens"]),
                _fmt_tok(b["cache_read"]),
                f"${b['cost_usd']:.4f}",
                model_str,
            )
            total_cost    += b["cost_usd"]
            total_out     += b["output_tokens"]
            total_cache_r += b["cache_read"]
            total_dur     += b["duration_s"]
            total_turns_c += b["turns"]

        ctbl.add_section()
        shown_label = f"[bold]Shown {len(shown_cmds)}[/bold]"
        ctbl.add_row(
            shown_label,
            "[bold]TOTAL[/bold]",
            "",
            "",
            f"[bold]{_fmt_duration(total_dur)}[/bold]",
            f"[bold]{int(total_turns_c):,}[/bold]",
            f"[bold cyan]{_fmt_tok(int(total_out))}[/bold cyan]",
            f"[bold green]{_fmt_tok(int(total_cache_r))}[/bold green]",
            f"[bold yellow]${total_cost:.4f}[/bold yellow]",
            "",
        )

        console.print(ctbl)
        console.print()
        console.print(
            "[dim]Cost = estimated USD based on published Anthropic pricing (input + output + cache). "
            "Start/End = local time of first/last assistant turn. "
            "Duration = wall-clock from first to last assistant turn.[/dim]\n"
            + (f"[dim]Run [cyan]pandawa usage --commands --limit 0[/cyan] to see all {len(all_cmds)} commands.[/dim]"
               if limit and len(all_cmds) > limit else "")
        )
        return

    # ---- default: per-session view ----
    sessions = [_parse_session_file(f) for f in jsonl_files]
    sessions = [s for s in sessions if s["output_tokens"] > 0]
    sessions_sorted = sorted(sessions, key=lambda s: s["date"] or "", reverse=True)

    shown = sessions_sorted if limit == 0 else sessions_sorted[:limit]

    total_turns = sum(s["turns"] for s in sessions)
    total_input = sum(s["input_tokens"] for s in sessions)
    total_output = sum(s["output_tokens"] for s in sessions)
    total_cache_r = sum(s["cache_read"] for s in sessions)
    total_cache_w = sum(s["cache_write"] for s in sessions)
    all_models = sorted({m for s in sessions for m in s["models"] if not m.startswith("<")})

    console.print()
    console.print(Panel(
        f"[dim]Project  [/dim] [cyan]{project_path}[/cyan]\n"
        f"[dim]Sessions [/dim] [bright_black]{sessions_dir}[/bright_black]\n"
        f"[dim]Found    [/dim] {len(sessions)} sessions with AI activity"
        + (f"  [dim](showing latest {len(shown)})[/dim]" if limit and len(sessions) > limit else ""),
        title="[bold]Claude Code Session Usage[/bold]",
        border_style="cyan",
        padding=(1, 2),
    ))

    tbl = Table(show_header=True, header_style="bold cyan", box=None, padding=(0, 1),
                show_edge=False)
    tbl.add_column("Date",       style="bright_black", min_width=10, no_wrap=True)
    tbl.add_column("Title / Session",                  min_width=16, max_width=26, no_wrap=True)
    tbl.add_column("Trn",        justify="right", style="dim",   min_width=5, no_wrap=True)
    tbl.add_column("Input",      justify="right",               min_width=6, no_wrap=True)
    tbl.add_column("Output",     justify="right",               min_width=6, no_wrap=True)
    tbl.add_column("Cache hit",  justify="right", style="green", min_width=9, no_wrap=True)
    tbl.add_column("Model",      style="bright_black",          min_width=11, no_wrap=True)

    for s in shown:
        if s["title"]:
            label = s["title"][:25] + "…" if len(s["title"]) > 25 else s["title"]
        else:
            label = f"[dim]{s['session_id'][:16]}[/dim]"
        real_models = [m for m in sorted(s["models"]) if not m.startswith("<")]
        short_models = [re.sub(r"-\d{8}$", "", m.replace("claude-", "")) for m in real_models]
        model_str = short_models[0] if len(short_models) == 1 else " / ".join(short_models)
        tbl.add_row(
            s["date"] or "—",
            label,
            str(s["turns"]),
            _fmt_tok(s["input_tokens"]),
            _fmt_tok(s["output_tokens"]),
            _fmt_tok(s["cache_read"]),
            model_str or "—",
        )

    short_all_models = [re.sub(r"-\d{8}$", "", m.replace("claude-", "")) for m in all_models]
    tbl.add_section()
    tbl.add_row(
        f"[bold]All {len(sessions)}[/bold]",
        "[bold]TOTAL[/bold]",
        f"[bold]{total_turns:,}[/bold]",
        f"[bold cyan]{_fmt_tok(total_input)}[/bold cyan]",
        f"[bold cyan]{_fmt_tok(total_output)}[/bold cyan]",
        f"[bold green]{_fmt_tok(total_cache_r)}[/bold green]",
        " / ".join(short_all_models) or "—",
    )

    console.print(tbl)
    console.print()
    console.print(
        "[dim]Cache hit = tokens read from cache (cheaper). Cache +new = tokens written to cache.[/dim]\n"
        "[dim]Tip: run [cyan]pandawa usage --commands[/cyan] to see per-command cost and duration.[/dim]\n"
        + (f"[dim]Run [cyan]pandawa usage --limit 0[/cyan] to see all {len(sessions)} sessions.[/dim]"
           if limit and len(sessions) > limit else "")
    )

# ---- `pandawa tui` command ----------------------------------------------------------------

@app.command()
def tui():
    """Launch the interactive TUI for plugin management, usage, and status."""
    from pandawa_cli.tui.app import PandawaTUIApp
    PandawaTUIApp(project_path=Path.cwd()).run()

# ---- `pandawa governance` command group --------------------------------------------------
# Manage the mutually-exclusive governance plugin type. The project's enabledPlugins is the
# source of truth; these commands keep invariant G1 (<= 1 governance active) and wire the
# runtime guard. Operate on the current working directory as the project.

governance_app = typer.Typer(
    help="Manage the active governance plugin (only one may be active per project).",
    no_args_is_help=True,
)
app.add_typer(governance_app, name="governance")

def _write_project_settings(project_path: Path, settings: dict) -> None:
    settings_path = project_path / ".claude" / "settings.json"
    settings_path.parent.mkdir(parents=True, exist_ok=True)
    settings_path.write_text(json.dumps(settings, indent=2) + "\n", encoding="utf-8")

# ---- shared plugin-management helpers (skill + governance) ------------------------------

def _set_plugin_enabled(project_path: Path, name: str, enabled: bool, *, marketplace: str = MARKETPLACE_NAME) -> None:
    """Set a plugin's enable bit in project settings.json (the activation control honored by
    Claude Code and read by the governance guard). Content download is separate (_plugin_install)."""
    settings = _load_project_settings(project_path)
    ep = settings.get("enabledPlugins") or {}
    ep[f"{name}@{marketplace}"] = enabled
    settings["enabledPlugins"] = ep
    _write_project_settings(project_path, settings)

def _project_marketplace_url(project_path: "Path | None", name: str = MARKETPLACE_NAME) -> "str | None":
    """The marketplace git URL the project is pointed at (.claude/settings.json
    extraKnownMarketplaces.<name>.source.url), or None when not configured."""
    if project_path is None:
        return None
    src = (_load_project_settings(project_path).get("extraKnownMarketplaces") or {}).get(name) or {}
    url = (src.get("source") or {}).get("url") if isinstance(src, dict) else None
    return url.strip() if isinstance(url, str) and url.strip() else None

def _resolve_marketplace_url(project_path: "Path | None" = None, name: str = MARKETPLACE_NAME) -> str:
    """Marketplace git URL precedence: env override > project pointer > built-in default."""
    return (os.getenv("PANDAWA_MARKETPLACE_URL")
            or _project_marketplace_url(project_path, name)
            or DEFAULT_MARKETPLACE_URL)

def _authenticated_clone_url(url: str, token: "str | None") -> str:
    """Embed a GitLab token into an https URL so Claude Code can clone a PRIVATE
    marketplace non-interactively. Leaves ssh/scp URLs, local paths, and URLs that
    already carry credentials untouched; returns the URL unchanged without a token."""
    if not token:
        return url
    try:
        parsed = urlparse(url)
    except Exception:
        return url
    if parsed.scheme not in ("http", "https") or not parsed.netloc or "@" in parsed.netloc:
        return url
    netloc = f"oauth2:{quote(token, safe='')}@{parsed.netloc}"
    return urlunparse(parsed._replace(netloc=netloc))

def _marketplace_registered(name: str) -> bool:
    """True if Claude Code already knows a marketplace called `name`."""
    rc, out, err = _run_claude(["plugin", "marketplace", "list"])
    if rc != 0:
        return False
    return bool(re.search(rf"(?m)^\s*[>❯*\-\s]*{re.escape(name)}\b", out or "")) or name in (out or "")

def _ensure_marketplace(name: str, url: str, *, token: "str | None" = None) -> "tuple[bool, str]":
    """Make sure Claude Code has the `name` marketplace registered AND fresh before an
    install. This is the gap that made `plugin install <x>@pandawa` fail with "not found in
    marketplace": pandawa only ever wrote extraKnownMarketplaces to settings.json, which the
    headless `claude plugin install` CLI does not auto-register. (ok, message)."""
    if _marketplace_registered(name):
        # Known already — refresh so newly-published plugins become visible. Best-effort.
        _run_claude(["plugin", "marketplace", "update", name])
        return (True, "")
    if not url:
        return (False, f"marketplace '{name}' is not registered in Claude Code and no URL is configured.")
    rc, out, err = _run_claude(["plugin", "marketplace", "add", _authenticated_clone_url(url, token)])
    if rc == 0 or _marketplace_registered(name):  # added now, or a concurrent add won the race
        _run_claude(["plugin", "marketplace", "update", name])
        return (True, (out or "").strip())
    detail = (err or out or "").strip()
    hint = "" if token else " (no GitLab token found — set GL_TOKEN/GITLAB_TOKEN for a private marketplace)"
    return (False, f"could not register marketplace '{name}' from {url}{hint}: {detail}" if detail
            else f"could not register marketplace '{name}' from {url}{hint}.")

def _plugin_install(name: str, *, marketplace: str = MARKETPLACE_NAME, scope: str = "project",
                    project: "Path | None" = None) -> "tuple[bool, str]":
    """Download/install plugin CONTENT to the local Claude Code store. (bool ok, message).

    Ensures the marketplace is registered with Claude Code first (and refreshed), so an
    install can never fail with "plugin not found in marketplace" just because the
    marketplace was only written to settings.json but never added to the CLI's store."""
    if _claude_exe() is None:
        return (False, "claude CLI not found — install Claude Code / add it to PATH to download plugins.")
    url = _resolve_marketplace_url(project, marketplace)
    ok, mp_msg = _ensure_marketplace(marketplace, url, token=_gitlab_token())
    if not ok:
        return (False, mp_msg)
    rc, out, err = _run_claude(["plugin", "install", f"{name}@{marketplace}", "--scope", scope])
    if rc is None:
        return (False, "claude CLI not found — install Claude Code / add it to PATH to download plugins.")
    if rc != 0:
        return (False, (err or out).strip() or f"`claude plugin install` failed (exit {rc}).")
    return (True, (out or "").strip())

def _plugin_uninstall(name: str, *, marketplace: str = MARKETPLACE_NAME) -> "tuple[bool, str]":
    """Remove plugin CONTENT from the local Claude Code store. (bool ok, message)."""
    rc, out, err = _run_claude(["plugin", "uninstall", f"{name}@{marketplace}"])
    if rc is None:
        return (False, "claude CLI not found — install Claude Code / add it to PATH.")
    if rc != 0:  # retry with the bare name (some versions key uninstall by name only)
        rc2, out2, err2 = _run_claude(["plugin", "uninstall", name])
        if rc2 == 0:
            return (True, (out2 or "").strip())
        return (False, (err or out).strip() or f"`claude plugin uninstall` failed (exit {rc}).")
    return (True, (out or "").strip())

def marketplace_catalog(*, url: "str | None" = None, cli_token: "str | None" = None,
                        client: "httpx.Client | None" = None) -> "tuple[str, dict[str, str]] | None":
    """(marketplace_name, {plugin: category}) from the live marketplace, or None when offline."""
    url = url or os.getenv("PANDAWA_MARKETPLACE_URL") or DEFAULT_MARKETPLACE_URL
    return fetch_marketplace_plugins(url, cli_token=cli_token, client=client)

def _print_plugin_table(col: str, rows: "list[tuple[str, str]]") -> None:
    table = Table(show_header=True, header_style="bold cyan", box=None, padding=(0, 2))
    table.add_column(col)
    table.add_column("Status")
    for name, status in rows:
        table.add_row(name, status)
    console.print(table)

@governance_app.command("refresh")
def governance_refresh(
    marketplace_url: str = typer.Option(None, "--marketplace-url", help="Override the marketplace git URL (or PANDAWA_MARKETPLACE_URL)."),
    gitlab_token: str = typer.Option(None, "--gitlab-token", help="GitLab token (or GL_TOKEN / GITLAB_TOKEN env var)."),
):
    """Sync the governance catalog from the marketplace (decoupled from CLI releases).

    Fetches only the marketplace index (.claude-plugin/marketplace.json) over the GitLab API
    and records which plugins are category=governance into .pandawa/governance-catalog.json. It
    does NOT download or install plugin content — that stays with Claude Code's `/plugin`.
    """
    project = Path.cwd()
    _timer = ProcessTimer("pandawa governance refresh")
    url = marketplace_url or os.getenv("PANDAWA_MARKETPLACE_URL") or DEFAULT_MARKETPLACE_URL
    before = set(governance_catalog_names(project))
    names = refresh_governance_catalog(project, url=url, cli_token=gitlab_token)
    if names is None:
        console.print(f"[red]Could not fetch the marketplace catalog[/red] from {url}.")
        console.print("[dim]Check your network and GitLab token (GL_TOKEN / --gitlab-token). "
                      "The existing cached catalog is unchanged.[/dim]")
        _timer.stop(status="failed", error="Could not fetch marketplace catalog")
        show_audit_panel(_timer, project_path=project, extra={"URL": url})
        raise typer.Exit(1)
    after = set(names)
    console.print(f"[green]Governance catalog refreshed[/green] from the marketplace.")
    console.print(f"Governance plugins: {', '.join(sorted(after)) or '(none)'}")
    added, removed = sorted(after - before), sorted(before - after)
    if added:
        console.print(f"[green]+ added:[/green] {', '.join(added)}")
    if removed:
        console.print(f"[yellow]- removed:[/yellow] {', '.join(removed)}")
    if not added and not removed:
        console.print("[dim](no change)[/dim]")
    _timer.stop()
    show_audit_panel(_timer, project_path=project,
                     extra={"URL": url, "Plugins": ", ".join(sorted(after)) or "(none)"})

@governance_app.command("list")
def governance_list(
    target: str = typer.Argument(None, help="Pass 'marketplace' to list ALL governance in the marketplace (installed + available)."),
):
    """List governance plugins INSTALLED locally (ready to `use`).

    `pandawa governance list marketplace` instead lists every governance plugin in the
    marketplace, marking which are already installed — install from there, then `use`.
    """
    project = Path.cwd()

    # ---- marketplace view: all governance in the marketplace, marked installed/active ----
    if target == "marketplace":
        cat = marketplace_catalog()
        if cat is None:
            console.print("[red]Could not reach the marketplace[/red] (offline or missing GitLab token).")
            console.print("[dim]Set GL_TOKEN and retry, or run `pandawa governance refresh` when online.[/dim]")
            raise typer.Exit(1)
        _, catalog = cat
        govs = sorted(n for n, c in catalog.items() if c == "governance")
        if not govs:
            console.print("[yellow]No governance plugins in the marketplace.[/yellow]")
            return
        installed = claude_installed_plugins() or {}
        active = set(active_governance_plugins(project))
        rows = []
        for n in govs:
            if n in active:
                rows.append((n, "[bold green]active[/bold green]"))
            elif n in installed:
                rows.append((n, "[green]installed[/green] [dim](inactive)[/dim]"))
            else:
                rows.append((n, "[dim]available — not installed[/dim]"))
        _print_plugin_table("Governance plugin (marketplace)", rows)
        console.print("[dim]Install with[/dim] [cyan]pandawa governance install <name>[/cyan][dim], then[/dim] [cyan]pandawa governance use <name>[/cyan][dim].[/dim]")
        return

    # ---- local view: governance plugins installed in this project, ready to use ----
    installed = claude_installed_plugins()
    gov_catalog = set(governance_catalog_names(project))
    active = set(active_governance_plugins(project))
    if installed is None:
        # claude CLI unavailable -> can't read the local store; show what settings says is active.
        console.print("[yellow]Cannot read the local plugin store[/yellow] (claude CLI not found).")
        if active:
            _print_plugin_table("Governance plugin (active, per settings)", [(n, "[bold green]active[/bold green]") for n in sorted(active)])
        console.print("[dim]Install the Claude Code CLI to manage the local store, or see[/dim] [cyan]pandawa governance list marketplace[/cyan][dim].[/dim]")
        return
    local = sorted((set(installed) & gov_catalog) | active)
    if not local:
        console.print("[yellow]No governance plugin is installed locally.[/yellow]")
        console.print("[dim]Browse + install:[/dim] [cyan]pandawa governance list marketplace[/cyan] [dim]→[/dim] [cyan]pandawa governance install <name>[/cyan].")
        return
    rows = []
    for n in local:
        if n in active and n not in installed:
            rows.append((n, "[yellow]active — content missing (run install)[/yellow]"))
        elif n in active:
            rows.append((n, "[bold green]active[/bold green]"))
        else:
            rows.append((n, "[green]installed[/green] [dim](inactive — `use` to activate)[/dim]"))
    _print_plugin_table("Governance plugin (local)", rows)
    if len(active) >= 2:
        console.print(f"\n[bold red]CONFLICT:[/bold red] {len(active)} governance plugins active "
                      f"({', '.join(sorted(active))}). Run [cyan]pandawa governance disable[/cyan] then "
                      "[cyan]pandawa governance use <name>[/cyan].")

@governance_app.command("install")
def governance_install(
    name: str = typer.Argument(..., help="Governance plugin to download to local (then `use` to activate)."),
    marketplace: str = typer.Option(MARKETPLACE_NAME, "--marketplace", help="Marketplace name."),
):
    """Download a governance plugin to the local store (does NOT activate it).

    Governance is download-then-use: this only fetches content. Activate exactly one with
    `pandawa governance use <name>` afterwards.
    """
    project = Path.cwd()
    _timer = ProcessTimer(f"pandawa governance install")
    _auto_refresh_catalog(project)
    configure_governance_guard(project, marketplace=marketplace)
    known = governance_catalog_names(project)
    if name not in known:
        console.print(f"[red]'{name}' is not a known governance plugin.[/red]")
        console.print(f"[dim]See[/dim] [cyan]pandawa governance list marketplace[/cyan][dim]; or `pandawa governance refresh` to sync.[/dim]")
        _timer.stop(status="failed", error=f"'{name}' is not a known governance plugin")
        show_audit_panel(_timer, project_path=project, extra={"Plugin": name})
        raise typer.Exit(1)
    ok, msg = _plugin_install(name, marketplace=marketplace, project=project)
    if not ok:
        console.print(f"[red]Install failed:[/red] {msg}")
        _timer.stop(status="failed", error=msg)
        show_audit_panel(_timer, project_path=project, extra={"Plugin": name})
        raise typer.Exit(1)
    _set_plugin_enabled(project, name, False, marketplace=marketplace)  # downloaded, NOT active
    console.print(f"[green]Downloaded[/green] [bold]{name}[/bold] to the local store (inactive).")
    console.print(f"Activate it with [cyan]pandawa governance use {name}[/cyan].")
    _timer.stop()
    show_audit_panel(_timer, project_path=project, extra={"Plugin": name, "Marketplace": marketplace})

@governance_app.command("uninstall")
def governance_uninstall(
    name: str = typer.Argument(..., help="Governance plugin to remove from the local store."),
    marketplace: str = typer.Option(MARKETPLACE_NAME, "--marketplace", help="Marketplace name."),
):
    """Remove a governance plugin from the local store (disables it first if active)."""
    project = Path.cwd()
    _timer = ProcessTimer("pandawa governance uninstall")
    if name in active_governance_plugins(project):
        _set_plugin_enabled(project, name, False, marketplace=marketplace)
        console.print(f"[dim]disabled active governance {name} first[/dim]")
    ok, msg = _plugin_uninstall(name, marketplace=marketplace)
    if not ok:
        console.print(f"[red]Uninstall failed:[/red] {msg}")
        _timer.stop(status="failed", error=msg)
        show_audit_panel(_timer, project_path=project, extra={"Plugin": name})
        raise typer.Exit(1)
    console.print(f"[green]Removed[/green] [bold]{name}[/bold] from the local store. [yellow]Restart Claude Code[/yellow] to apply.")
    _timer.stop()
    show_audit_panel(_timer, project_path=project, extra={"Plugin": name, "Marketplace": marketplace})

@governance_app.command("status")
def governance_status():
    """Show the active governance plugin and validate the one-active invariant."""
    project = Path.cwd()
    active = active_governance_plugins(project)
    if not active:
        console.print("[yellow]No governance plugin is active.[/yellow] "
                      "Enable one with [cyan]pandawa governance use <name>[/cyan].")
        return
    if len(active) == 1:
        console.print(f"[green]Active governance:[/green] [bold]{active[0]}[/bold]")
        return
    console.print(f"[bold red]CONFLICT — {len(active)} governance plugins active:[/bold red] {', '.join(active)}")
    console.print("Resolve: [cyan]pandawa governance disable[/cyan] then [cyan]pandawa governance use <name>[/cyan], "
                  "and restart Claude Code.")
    raise typer.Exit(1)

@governance_app.command("use")
def governance_use(
    name: str = typer.Argument(..., help="Governance plugin to activate (e.g. tmf-oda-constitution)."),
    force: bool = typer.Option(False, "--force", "-f", help="Swap directly even if another governance is active (skip disable-first)."),
    marketplace: str = typer.Option(MARKETPLACE_NAME, "--marketplace", help="Marketplace name used in enabledPlugins keys."),
):
    """Activate exactly one governance plugin, disabling any other.

    Disable-first by default: if a different governance is active this refuses and asks you
    to disable it first; pass --force to swap in one step. Requires a Claude Code restart.
    """
    project = Path.cwd()
    _timer = ProcessTimer("pandawa governance use")
    # Refresh the catalog from the live marketplace (best-effort) so a newly-contributed
    # governance plugin is recognized, then wire the guard + catalog (idempotent) so
    # enforcement exists even in a project created before governance support / `pandawa init`.
    _auto_refresh_catalog(project)
    configure_governance_guard(project, marketplace=marketplace)
    known = governance_catalog_names(project)
    if name not in known:
        console.print(f"[red]'{name}' is not a known governance plugin.[/red]")
        console.print(f"[dim]See[/dim] [cyan]pandawa governance list marketplace[/cyan][dim]; or `pandawa governance refresh` to sync.[/dim]")
        _timer.stop(status="failed", error=f"'{name}' is not a known governance plugin")
        show_audit_panel(_timer, project_path=project, extra={"Plugin": name})
        raise typer.Exit(1)

    # Download-then-use: require the plugin to be installed locally first.
    installed = claude_installed_plugins()
    if installed is not None and name not in installed:
        console.print(f"[yellow]'{name}' is not installed locally yet.[/yellow]")
        console.print(f"Download it first: [cyan]pandawa governance install {name}[/cyan], then re-run [cyan]pandawa governance use {name}[/cyan].")
        _timer.stop(status="failed", error=f"'{name}' is not installed locally")
        show_audit_panel(_timer, project_path=project, extra={"Plugin": name})
        raise typer.Exit(1)
    # (installed is None -> claude CLI unavailable; proceed on settings only, can't verify.)

    active = active_governance_plugins(project)
    if active == [name]:
        console.print(f"[green]'{name}' is already the active governance.[/green]")
        _timer.stop()
        show_audit_panel(_timer, project_path=project, extra={"Plugin": name, "Action": "already active"})
        return
    others = [a for a in active if a != name]
    if others and not force:
        console.print(f"[yellow]'{others[0]}' is currently active.[/yellow] Governance is mutually exclusive.")
        console.print(f"Disable it first: [cyan]pandawa governance disable[/cyan], then [cyan]pandawa governance use {name}[/cyan].")
        console.print("[dim]Or swap in one step with[/dim] [cyan]--force[/cyan].")
        _timer.stop(status="failed", error=f"'{others[0]}' is already active")
        show_audit_panel(_timer, project_path=project, extra={"Plugin": name})
        raise typer.Exit(1)

    settings = _load_project_settings(project)
    enabled = settings.get("enabledPlugins") or {}
    for gov in known:  # disable every known governance, enable only the chosen one
        enabled[f"{gov}@{marketplace}"] = (gov == name)
    settings["enabledPlugins"] = enabled
    _write_project_settings(project, settings)

    if others:
        console.print(f"[green]disabled[/green] {', '.join(others)}")
    console.print(f"[green]enabled[/green]  [bold]{name}[/bold]")
    console.print(f"\nActive governance is now [bold]{name}[/bold]. [yellow]Restart Claude Code[/yellow] to load it.")
    _timer.stop()
    show_audit_panel(_timer, project_path=project,
                     extra={"Plugin": name, "Disabled": ", ".join(others) or "none"})

@governance_app.command("disable")
def governance_disable(
    name: str = typer.Argument(None, help="Specific governance plugin to disable (default: all currently active)."),
    marketplace: str = typer.Option(MARKETPLACE_NAME, "--marketplace", help="Marketplace name used in enabledPlugins keys."),
):
    """Disable the active governance plugin (or a named one). Leaves zero active by default."""
    project = Path.cwd()
    _timer = ProcessTimer("pandawa governance disable")
    known = set(governance_catalog_names(project))
    if name and name not in known:
        console.print(f"[red]'{name}' is not a known governance plugin.[/red]")
        _timer.stop(status="failed", error=f"'{name}' is not a known governance plugin")
        show_audit_panel(_timer, project_path=project, extra={"Plugin": name or "(all)"})
        raise typer.Exit(1)
    targets = [name] if name else active_governance_plugins(project)
    if not targets:
        console.print("[dim]No active governance to disable.[/dim]")
        _timer.stop()
        show_audit_panel(_timer, project_path=project, extra={"Action": "nothing to disable"})
        return
    settings = _load_project_settings(project)
    enabled = settings.get("enabledPlugins") or {}
    changed = []
    for gov in targets:
        key = f"{gov}@{marketplace}"
        if enabled.get(key) is True:
            enabled[key] = False
            changed.append(gov)
    settings["enabledPlugins"] = enabled
    _write_project_settings(project, settings)
    if changed:
        console.print(f"[green]disabled[/green] {', '.join(changed)}")
        console.print("[yellow]Restart Claude Code[/yellow] to apply.")
    else:
        console.print("[dim]Nothing to disable.[/dim]")
    _timer.stop()
    show_audit_panel(_timer, project_path=project,
                     extra={"Disabled": ", ".join(changed) or "none"})

# ---- `pandawa skill` command group -------------------------------------------------------
# Skill plugins are NOT exclusive: install on demand, many may be enabled at once. This is
# a category-filtered view over the same `claude plugin` store — no policy, no guard.

skill_app = typer.Typer(
    help="Manage skill plugins (install on demand; many can be active at once).",
    no_args_is_help=True,
)
app.add_typer(skill_app, name="skill")

def _skill_local_plugins(project_path: Path) -> "dict[str, bool] | None":
    """Installed skill plugins = installed plugins that are NOT governance.
    Returns name->enabled, or None if the local store can't be read (claude CLI missing)."""
    installed = claude_installed_plugins()
    if installed is None:
        return None
    gov = set(governance_catalog_names(project_path))
    return {n: en for n, en in installed.items() if n not in gov}

@skill_app.command("list")
def skill_list(
    target: str = typer.Argument(None, help="Pass 'marketplace' to list ALL skill plugins (installed + available)."),
):
    """List skill plugins INSTALLED locally (enabled = ready to use).

    `pandawa skill list marketplace` lists every skill plugin in the marketplace, marking which
    are already installed.
    """
    project = Path.cwd()
    if target == "marketplace":
        cat = marketplace_catalog()
        if cat is None:
            console.print("[red]Could not reach the marketplace[/red] (offline or missing GitLab token).")
            raise typer.Exit(1)
        _, catalog = cat
        skills = sorted(n for n, c in catalog.items() if c != "governance")
        if not skills:
            console.print("[yellow]No skill plugins in the marketplace.[/yellow]")
            return
        installed = claude_installed_plugins() or {}
        rows = [(n, "[green]installed[/green]" if n in installed else "[dim]available — not installed[/dim]") for n in skills]
        _print_plugin_table("Skill plugin (marketplace)", rows)
        console.print("[dim]Install with[/dim] [cyan]pandawa skill install <name>[/cyan][dim] — ready to use immediately.[/dim]")
        return
    local = _skill_local_plugins(project)
    if local is None:
        console.print("[yellow]Cannot read the local plugin store[/yellow] (claude CLI not found).")
        console.print("[dim]See[/dim] [cyan]pandawa skill list marketplace[/cyan][dim].[/dim]")
        return
    if not local:
        console.print("[yellow]No skill plugin is installed locally.[/yellow]")
        console.print("[dim]Browse + install:[/dim] [cyan]pandawa skill list marketplace[/cyan] [dim]→[/dim] [cyan]pandawa skill install <name>[/cyan].")
        return
    rows = [(n, "[bold green]enabled[/bold green]" if en else "[dim]disabled[/dim]") for n, en in sorted(local.items())]
    _print_plugin_table("Skill plugin (local)", rows)

@skill_app.command("install")
def skill_install(
    name: str = typer.Argument(..., help="Skill plugin to download and enable."),
    marketplace: str = typer.Option(MARKETPLACE_NAME, "--marketplace", help="Marketplace name."),
):
    """Download a skill plugin and enable it (ready to use immediately)."""
    project = Path.cwd()
    _timer = ProcessTimer("pandawa skill install")
    if name in set(governance_catalog_names(project)):
        console.print(f"[yellow]'{name}' is a governance plugin.[/yellow] Use [cyan]pandawa governance install {name}[/cyan] instead.")
        _timer.stop(status="failed", error=f"'{name}' is a governance plugin, not a skill")
        show_audit_panel(_timer, project_path=project, extra={"Plugin": name})
        raise typer.Exit(1)
    ok, msg = _plugin_install(name, marketplace=marketplace, project=project)
    if not ok:
        console.print(f"[red]Install failed:[/red] {msg}")
        _timer.stop(status="failed", error=msg)
        show_audit_panel(_timer, project_path=project, extra={"Plugin": name})
        raise typer.Exit(1)
    _set_plugin_enabled(project, name, True, marketplace=marketplace)
    console.print(f"[green]Installed + enabled[/green] [bold]{name}[/bold]. [yellow]Restart Claude Code[/yellow] to load it.")
    _timer.stop()
    show_audit_panel(_timer, project_path=project, extra={"Plugin": name, "Marketplace": marketplace})

@skill_app.command("uninstall")
def skill_uninstall(
    name: str = typer.Argument(..., help="Skill plugin to remove from the local store."),
    marketplace: str = typer.Option(MARKETPLACE_NAME, "--marketplace", help="Marketplace name."),
):
    """Remove a skill plugin from the local store."""
    project = Path.cwd()
    _timer = ProcessTimer("pandawa skill uninstall")
    _set_plugin_enabled(project, name, False, marketplace=marketplace)
    ok, msg = _plugin_uninstall(name, marketplace=marketplace)
    if not ok:
        console.print(f"[red]Uninstall failed:[/red] {msg}")
        _timer.stop(status="failed", error=msg)
        show_audit_panel(_timer, project_path=project, extra={"Plugin": name})
        raise typer.Exit(1)
    console.print(f"[green]Removed[/green] [bold]{name}[/bold]. [yellow]Restart Claude Code[/yellow] to apply.")
    _timer.stop()
    show_audit_panel(_timer, project_path=project, extra={"Plugin": name, "Marketplace": marketplace})

@skill_app.command("enable")
def skill_enable(
    name: str = typer.Argument(..., help="Installed skill plugin to enable."),
    marketplace: str = typer.Option(MARKETPLACE_NAME, "--marketplace", help="Marketplace name."),
):
    """Enable an installed skill plugin (many may be enabled at once)."""
    project = Path.cwd()
    _timer = ProcessTimer("pandawa skill enable")
    _set_plugin_enabled(project, name, True, marketplace=marketplace)
    console.print(f"[green]enabled[/green] [bold]{name}[/bold]. [yellow]Restart Claude Code[/yellow] to apply.")
    _timer.stop()
    show_audit_panel(_timer, project_path=project, extra={"Plugin": name})

@skill_app.command("disable")
def skill_disable(
    name: str = typer.Argument(..., help="Skill plugin to disable (keeps it installed)."),
    marketplace: str = typer.Option(MARKETPLACE_NAME, "--marketplace", help="Marketplace name."),
):
    """Disable a skill plugin without uninstalling it."""
    project = Path.cwd()
    _timer = ProcessTimer("pandawa skill disable")
    _set_plugin_enabled(project, name, False, marketplace=marketplace)
    console.print(f"[green]disabled[/green] [bold]{name}[/bold]. [yellow]Restart Claude Code[/yellow] to apply.")
    _timer.stop()
    show_audit_panel(_timer, project_path=project, extra={"Plugin": name})

# ---- `pandawa run` command group -----------------------------------------------------------
# Wraps /pandawa.* skills via `claude --print --output-format json` so each invocation
# captures real token usage (input, output, cache) and model name from the JSON response.

_PANDAWA_SKILLS = {
    "constitution": "/pandawa.constitution",
    "brd":          "/pandawa.brd",
    "specify":      "/pandawa.specify",
    "plan":         "/pandawa.plan",
    "tasks":        "/pandawa.tasks",
    "implement":    "/pandawa.implement",
    "clarify":      "/pandawa.clarify",
    "analyze":      "/pandawa.analyze",
    "checklist":    "/pandawa.checklist",
    "test":         "/pandawa.test",
    "redesign":     "/pandawa.redesign",
    "deploy":       "/pandawa.deploy",
    "operate":      "/pandawa.operate",
    "postmortem":   "/pandawa.postmortem",
}

run_app = typer.Typer(
    help="Run /pandawa.* skills via Claude and capture token usage.",
    no_args_is_help=True,
)
app.add_typer(run_app, name="run")

# ---- pandawa profile -------------------------------------------------------------------------

profile_app = typer.Typer(
    help="Manage domain profiles — list available profiles, check for updates, set local paths.",
    no_args_is_help=True,
)
app.add_typer(profile_app, name="profile")


def _parse_semver(version: "str | None") -> "tuple[int, int, int] | None":
    """Parse a strict MAJOR.MINOR.PATCH string, or None if it doesn't match (e.g. missing,
    pre-1.0-field profile, or a hand-typed non-semver string) — callers treat None as
    "can't compare", not as "outdated"."""
    if not version:
        return None
    m = re.match(r"^(\d+)\.(\d+)\.(\d+)$", version)
    if not m:
        return None
    return tuple(int(x) for x in m.groups())


@profile_app.command("list")
def profile_list() -> None:
    """List all available domain profiles (best-effort refresh from `main` first)."""
    _auto_refresh_profile_catalog()
    profile_config = _effective_profile_config()

    table = Table(
        show_header=True,
        header_style="bold cyan",
        box=None,
        show_edge=False,
        padding=(0, 1),
    )
    table.add_column("Key", style="bold", min_width=22)
    table.add_column("Name", min_width=30)
    table.add_column("Version", style="dim")
    table.add_column("Local path", style="dim")

    for key, cfg in profile_config.items():
        local = _get_profile_local_path(key)
        path_str = str(local) if local else "[dim]— (download from GitLab)[/dim]"
        table.add_row(key, cfg["name"], cfg.get("version") or "[dim]—[/dim]", path_str)

    console.print()
    console.print(table)
    console.print()
    console.print("[dim]Use [bold]pandawa profile refresh[/bold] to sync with the latest published profiles.[/dim]")
    console.print("[dim]Use [bold]pandawa profile set-local <key> <path>[/bold] to set a local path for a profile.[/dim]")
    console.print("[dim]Use [bold]pandawa init --profile <key>[/bold] to scaffold a project with a profile.[/dim]")
    console.print("[dim]Inside a project that already has a profile installed, use [bold]pandawa profile status[/bold] "
                  "to check for updates.[/dim]")


@profile_app.command("refresh")
def profile_refresh(
    gitlab_token: str = typer.Option(None, "--gitlab-token", help="GitLab token (or GL_TOKEN / GITLAB_TOKEN env var)."),
) -> None:
    """Sync the domain profile catalog from `main` (decoupled from CLI releases).

    Fetches only `profiles.json` plus each profile's small `profile.json` and caches
    the result locally. It does NOT download any profile content — that still happens on
    `pandawa init --profile`.
    """
    _timer = ProcessTimer("pandawa profile refresh")
    before = set(_effective_profile_config().keys())
    profiles = refresh_profile_catalog(cli_token=gitlab_token)
    if profiles is None:
        console.print("[red]Could not fetch the profile catalog[/red] from pandawa-marketplace-tooling's `main` (profiles.json).")
        console.print("[dim]Check your network and GitLab token (GL_TOKEN / --gitlab-token). "
                      "The existing cached catalog is unchanged.[/dim]")
        _timer.stop(status="failed", error="Could not fetch profile catalog")
        show_audit_panel(_timer)
        raise typer.Exit(1)
    after = set(_effective_profile_config().keys())
    console.print("[green]Profile catalog refreshed[/green] from pandawa-marketplace-tooling's `main` (profiles.json).")
    console.print(f"Profiles: {', '.join(sorted(after)) or '(none)'}")
    added, removed = sorted(after - before), sorted(before - after)
    if added:
        console.print(f"[green]+ added:[/green] {', '.join(added)}")
    if removed:
        console.print(f"[yellow]- removed:[/yellow] {', '.join(removed)}")
    if not added and not removed:
        console.print("[dim](no change)[/dim]")
    _timer.stop()
    show_audit_panel(_timer, extra={"Profiles": ", ".join(sorted(after)) or "(none)"})


@profile_app.command("set-local")
def profile_set_local(
    profile_key: str = typer.Argument(..., help="Profile key (e.g. tmforum-oda-door-v3)"),
    path: str = typer.Argument(..., help="Absolute path to the local profile directory"),
) -> None:
    """Save a local directory path for a profile so pandawa init uses it automatically."""
    _auto_refresh_profile_catalog()
    profile_config = _effective_profile_config()
    if profile_key not in profile_config:
        console.print(f"[red]Error:[/red] Unknown profile '{profile_key}'. Available: {', '.join(profile_config.keys())}")
        console.print("[dim]Authoring a brand new profile that hasn't merged to pandawa-marketplace-tooling's "
                      "profiles.json yet? Use[/dim] [cyan]pandawa init --profile <key> --profile-path <dir>[/cyan][dim] directly instead.[/dim]")
        raise typer.Exit(1)
    p = Path(path).resolve()
    if not p.is_dir():
        console.print(f"[red]Error:[/red] Path does not exist or is not a directory: {p}")
        raise typer.Exit(1)
    _PROFILE_LOCAL_PATHS_FILE.parent.mkdir(parents=True, exist_ok=True)
    saved: dict = {}
    if _PROFILE_LOCAL_PATHS_FILE.exists():
        try:
            saved = json.loads(_PROFILE_LOCAL_PATHS_FILE.read_text())
        except Exception:
            pass
    saved[profile_key] = str(p)
    _PROFILE_LOCAL_PATHS_FILE.write_text(json.dumps(saved, indent=2))
    console.print(f"[green]Saved:[/green] {profile_key} → {p}")
    console.print(f"[dim]Config stored at {_PROFILE_LOCAL_PATHS_FILE}[/dim]")


def _profile_status_rows(project_path: Path, profile_config: "dict | None" = None) -> "list[dict]":
    """Diff this project's locked profile version(s) against the live catalog.

    Returns one dict per locked profile: {id, installed_version, latest_version, status,
    source}, status one of "local" (installed from --profile-path, not comparable),
    "unknown" (missing/non-semver version on either side), "update_available",
    "ahead" (installed is newer than the catalog — a stale/rolled-back cache), or
    "up_to_date". Empty list if this project has no `.pandawa/profile-lock.json` entries.

    Shared by the CLI `profile status` command and the TUI's StatusPane so the comparison
    rule lives in exactly one place. Does not refresh the catalog itself — callers that want
    a live comparison should call `_auto_refresh_profile_catalog()` first (both current
    callers do); pass a pre-fetched `profile_config` to skip re-reading the cache file.
    """
    locked = _read_profile_lock(project_path).get("profiles", {})
    if not locked:
        return []
    profile_config = profile_config if profile_config is not None else _effective_profile_config()

    rows = []
    for profile_id, entry in locked.items():
        installed_version = entry.get("version")
        if entry.get("ref") == "local":
            rows.append({
                "id": profile_id, "installed_version": installed_version,
                "latest_version": None, "status": "local", "source": entry.get("source"),
            })
            continue
        latest_version = profile_config.get(profile_id, {}).get("version")
        installed_t = _parse_semver(installed_version)
        latest_t = _parse_semver(latest_version)
        if installed_t is None or latest_t is None:
            status = "unknown"
        elif latest_t > installed_t:
            status = "update_available"
        elif latest_t < installed_t:
            status = "ahead"
        else:
            status = "up_to_date"
        rows.append({
            "id": profile_id, "installed_version": installed_version,
            "latest_version": latest_version, "status": status, "source": None,
        })
    return rows


@profile_app.command("status")
def profile_status() -> None:
    """Compare profile(s) installed in this project against the latest published version."""
    project_path = Path.cwd()
    _auto_refresh_profile_catalog()
    rows = _profile_status_rows(project_path)
    if not rows:
        console.print("[yellow]No domain profile installed in this project[/yellow] "
                      "(no `.pandawa/profile-lock.json`).")
        console.print("[dim]Run [bold]pandawa init --profile <key>[/bold] to install one.[/dim]")
        return

    table = Table(
        show_header=True,
        header_style="bold cyan",
        box=None,
        show_edge=False,
        padding=(0, 1),
    )
    table.add_column("Key", style="bold", min_width=22)
    table.add_column("Installed", min_width=12)
    table.add_column("Latest", min_width=12)
    table.add_column("Status")

    _STATUS_LABELS = {
        "unknown": "[dim]unknown — run `pandawa profile refresh`[/dim]",
        "update_available": "[yellow]update available[/yellow]",
        "ahead": "[dim]ahead of catalog[/dim]",
        "up_to_date": "[green]up to date[/green]",
    }
    any_update = False
    for row in rows:
        if row["status"] == "local":
            status_label = f"[dim]local source ({row['source'] or '?'}) — not compared[/dim]"
        else:
            status_label = _STATUS_LABELS[row["status"]]
            any_update = any_update or row["status"] == "update_available"
        table.add_row(row["id"], row["installed_version"] or "[dim]—[/dim]",
                      row["latest_version"] or "[dim]—[/dim]", status_label)

    console.print()
    console.print(table)
    console.print()
    if any_update:
        console.print("[dim]Run [bold]pandawa profile update <key>[/bold] to fetch the latest content.[/dim]")


@profile_app.command("update")
def profile_update(
    profile_key: str = typer.Argument(..., help="Profile key already installed in this project (see `pandawa profile status`)"),
    ai_assistant: str = typer.Option(None, "--ai", help="AI assistant this project uses (auto-detected from an existing instruction file if omitted)"),
    profile_path: str = typer.Option(None, "--profile-path", help="Local directory to use as profile source instead of downloading (for development/testing)"),
    gitlab_token: str = typer.Option(None, "--gitlab-token", help="GitLab token (or GL_TOKEN / GITLAB_TOKEN environment variable)"),
    debug: bool = typer.Option(False, "--debug", help="Show verbose diagnostic output for network and extraction failures"),
) -> None:
    """Re-fetch a profile already installed in this project, overwriting it with the latest `main`.

    This is the same content path as `pandawa init --profile`, scoped to a single profile that's
    already present — it does not touch anything else `init` would (templates, git, guardrails).
    It also only refreshes `.pandawa/profiles/<key>/` itself (plus the Claude sub-agent file);
    the one-time block already injected into your agent's instruction file (`CLAUDE.md`, etc.)
    and `.pandawa/memory/constitution.md` is left as-is if it already mentions this profile —
    same idempotency rule `pandawa init --here --force` already follows.
    """
    project_path = Path.cwd()
    profile_dest = project_path / ".pandawa" / "profiles" / profile_key
    if not profile_dest.is_dir():
        console.print(f"[red]Error:[/red] Profile '{profile_key}' is not installed in this project "
                      f"(no [dim]{profile_dest}[/dim]).")
        console.print(f"[dim]Run [bold]pandawa init --profile {profile_key}[/bold] to install it first.[/dim]")
        raise typer.Exit(1)

    # Missing from the lock is expected for a project whose profile predates this lockfile
    # feature — proceed anyway (the directory check above is the real gate) and this update
    # backfills the lock entry, same as any other update.
    locked = _read_profile_lock(project_path).get("profiles", {})
    old_version = locked.get(profile_key, {}).get("version")

    selected_ai = ai_assistant
    if selected_ai and selected_ai not in AGENT_CONFIG:
        console.print(f"[red]Error:[/red] Invalid AI assistant '{selected_ai}'. Choose from: {', '.join(AGENT_CONFIG.keys())}")
        raise typer.Exit(1)
    if not selected_ai:
        # Same project, same agent it was installed for — detect from whichever instruction
        # file `init`/a previous `update` already wrote, so callers don't have to re-specify it.
        for key, instruction_rel in _AGENT_INSTRUCTION_FILES.items():
            if (project_path / instruction_rel).exists():
                selected_ai = key
                break
        selected_ai = selected_ai or "claude"

    local_profile_path = Path(profile_path).resolve() if profile_path else None

    _timer = ProcessTimer("pandawa profile update")
    _auto_refresh_profile_catalog()
    try:
        download_and_extract_profile(
            project_path, profile_key, selected_ai,
            local_path=local_profile_path, verbose=True,
            debug=debug, gitlab_token=gitlab_token,
        )
    except Exception as e:
        console.print(f"[red]Error updating profile:[/red] {e}")
        _timer.stop(status="failed", error=str(e))
        show_audit_panel(_timer, project_path=project_path)
        raise typer.Exit(1)

    new_version = _read_profile_lock(project_path).get("profiles", {}).get(profile_key, {}).get("version")
    if old_version and new_version and old_version != new_version:
        console.print(f"[green]Updated {profile_key}:[/green] {old_version} → {new_version}")
    elif new_version:
        console.print(f"[green]Refreshed {profile_key}[/green] (version {new_version} — content re-synced from `main`)")
    else:
        console.print(f"[green]Refreshed {profile_key}[/green] (content re-synced from `main`)")
    _timer.stop()
    show_audit_panel(_timer, project_path=project_path, profile=profile_key)


def _run_claude_ai(
    skill_command: str,
    goal: str = "",
    timeout: int = 600,
) -> "tuple[str, dict | None, dict | None, float | None, bool]":
    """Call `claude --print --output-format json '<skill_command> <goal>'`.

    Returns (result_text, usage, model_usage, total_cost_usd, is_error).
    Usage keys: input_tokens, output_tokens, cache_read_input_tokens, cache_creation_input_tokens.
    Model_usage: {"model-id": {inputTokens, outputTokens, cacheReadInputTokens, costUSD, ...}}.
    """
    exe = _claude_exe()
    if not exe:
        return ("claude CLI not found — install Claude Code and add it to PATH.", None, None, None, True)

    prompt = f"{skill_command} {goal}".strip()
    try:
        p = subprocess.run(
            [exe, "--print", "--output-format", "json", prompt],
            capture_output=True, text=True, timeout=timeout,
            cwd=str(Path.cwd()),
        )
    except subprocess.TimeoutExpired:
        return (f"Timed out after {timeout}s.", None, None, None, True)
    except Exception as exc:
        return (str(exc), None, None, None, True)

    raw = (p.stdout or "").strip()
    if p.returncode != 0 and not raw:
        return ((p.stderr or "").strip() or f"claude exited {p.returncode}", None, None, None, True)

    try:
        data = json.loads(raw)
    except json.JSONDecodeError:
        return (raw, None, None, None, p.returncode != 0)

    result_text = data.get("result", "")
    usage = data.get("usage")
    model_usage = data.get("modelUsage")
    total_cost = data.get("total_cost_usd")
    is_err = data.get("is_error", False) or p.returncode != 0
    return (result_text, usage, model_usage, total_cost, is_err)


def _run_skill_command(skill_key: str, goal: str) -> None:
    """Shared implementation for all `pandawa run <skill>` subcommands."""
    project = Path.cwd()
    skill_cmd = _PANDAWA_SKILLS[skill_key]
    _timer = ProcessTimer(f"pandawa run {skill_key}")

    if _claude_exe() is None:
        console.print("[red]claude CLI not found.[/red] Install Claude Code and add it to PATH.")
        raise typer.Exit(1)

    with Progress(SpinnerColumn(), TextColumn(f"[cyan]Running {skill_cmd}…[/cyan]"), transient=True, console=console) as progress:
        progress.add_task("run")
        result_text, usage, model_usage, total_cost, is_err = _run_claude_ai(skill_cmd, goal)

    if result_text:
        console.print()
        console.print(result_text)

    status = "failed" if is_err else "success"
    error_msg = result_text if is_err else None
    _timer.stop(status=status, error=error_msg)
    show_audit_panel(
        _timer,
        project_path=project,
        usage=usage,
        model_usage=model_usage,
        total_cost=total_cost,
    )
    if is_err:
        raise typer.Exit(1)


@run_app.command("constitution")
def run_constitution(goal: str = typer.Argument("", help="Optional goal or context to pass to /pandawa.constitution")):
    """Run /pandawa.constitution and report token usage."""
    _run_skill_command("constitution", goal)

@run_app.command("brd")
def run_brd(goal: str = typer.Argument("", help="Optional scope/focus to pass to /pandawa.brd")):
    """Run /pandawa.brd — reverse-engineer a BRD from an existing codebase."""
    _run_skill_command("brd", goal)

@run_app.command("specify")
def run_specify(goal: str = typer.Argument("", help="Optional goal or context to pass to /pandawa.specify")):
    """Run /pandawa.specify and report token usage."""
    _run_skill_command("specify", goal)

@run_app.command("plan")
def run_plan(goal: str = typer.Argument("", help="Optional goal or context to pass to /pandawa.plan")):
    """Run /pandawa.plan and report token usage."""
    _run_skill_command("plan", goal)

@run_app.command("tasks")
def run_tasks(goal: str = typer.Argument("", help="Optional goal or context to pass to /pandawa.tasks")):
    """Run /pandawa.tasks and report token usage."""
    _run_skill_command("tasks", goal)

@run_app.command("implement")
def run_implement(goal: str = typer.Argument("", help="Optional goal or context to pass to /pandawa.implement")):
    """Run /pandawa.implement and report token usage."""
    _run_skill_command("implement", goal)

@run_app.command("clarify")
def run_clarify(goal: str = typer.Argument("", help="Optional goal or context to pass to /pandawa.clarify")):
    """Run /pandawa.clarify and report token usage."""
    _run_skill_command("clarify", goal)

@run_app.command("analyze")
def run_analyze(goal: str = typer.Argument("", help="Optional goal or context to pass to /pandawa.analyze")):
    """Run /pandawa.analyze and report token usage."""
    _run_skill_command("analyze", goal)

@run_app.command("checklist")
def run_checklist(goal: str = typer.Argument("", help="Optional goal or context to pass to /pandawa.checklist")):
    """Run /pandawa.checklist and report token usage."""
    _run_skill_command("checklist", goal)

@run_app.command("test")
def run_test(goal: str = typer.Argument("", help="Optional target path or context to pass to /pandawa.test")):
    """Run /pandawa.test — generate missing unit tests and check SonarQube compliance."""
    _run_skill_command("test", goal)

@run_app.command("redesign")
def run_redesign(goal: str = typer.Argument("", help="Redesign target and intent to pass to /pandawa.redesign")):
    """Run /pandawa.redesign — incrementally rework one part of an implemented feature."""
    _run_skill_command("redesign", goal)

@run_app.command("deploy")
def run_deploy(goal: str = typer.Argument("", help="Optional deployment scope/target to pass to /pandawa.deploy")):
    """Run /pandawa.deploy — prepare deployment automation (containerization, CI/CD, config)."""
    _run_skill_command("deploy", goal)

@run_app.command("operate")
def run_operate(goal: str = typer.Argument("", help="Optional mode/target to pass to /pandawa.operate")):
    """Run /pandawa.operate — wire observability, detect anomalies, and resolve incidents."""
    _run_skill_command("operate", goal)

@run_app.command("postmortem")
def run_postmortem(goal: str = typer.Argument("", help="Incident/learning summary to pass to /pandawa.postmortem")):
    """Run /pandawa.postmortem — feed production learnings back into the spec and constitution."""
    _run_skill_command("postmortem", goal)


def main():
    app()

if __name__ == "__main__":
    main()

