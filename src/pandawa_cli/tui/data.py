"""Data-layer wrappers around pandawa_cli helpers, for the TUI.

Every function here returns plain data (dataclasses/tuples) instead of
printing to a Rich console or raising typer.Exit(1), so Textual widgets can
decide how to present results. No plugin/marketplace/usage logic is
reimplemented — this module only calls the existing functions in
`pandawa_cli` and reshapes their output.
"""
from __future__ import annotations

import os
import shutil
import subprocess
from dataclasses import dataclass
from pathlib import Path

from pandawa_cli import (
    AGENT_CONFIG,
    BASELINE_DENY_RULES,
    DEFAULT_MARKETPLACE_URL,
    MARKETPLACE_BASELINE_PLUGINS,
    SCRIPT_TYPE_CHOICES,
    StepTracker,
    active_governance_plugins,
    check_tool,
    claude_installed_plugins,
    _get_client,
    configure_governance_guard,
    configure_guardrails,
    configure_marketplace,
    download_and_extract_profile,
    download_and_extract_template,
    ensure_executable_scripts,
    governance_catalog_names,
    init_git_repo,
    is_git_repo,
    marketplace_catalog,
    refresh_governance_catalog,
    refresh_profile_catalog,
    scaffold_project_context,
    _auto_refresh_profile_catalog,
    _claude_sessions_dir,
    _effective_profile_config,
    _estimate_cost,
    _fmt_duration,
    _fmt_local_time,
    _get_profile_local_path,
    _gitlab_auth_headers,
    _gitlab_token,
    _marketplace_raw_file_url,
    _parse_session_commands,
    _parse_session_file,
    _plugin_install,
    _plugin_uninstall,
    _profile_status_rows,
    _run_claude_ai,
    _pandawa_version_str,
    _set_plugin_enabled,
    _PANDAWA_SKILLS,
)


@dataclass
class PluginRow:
    name: str
    category: str  # "governance" | "skill"
    installed: bool
    enabled: bool


@dataclass
class PluginsSnapshot:
    rows: list[PluginRow]
    store_readable: bool  # False if the `claude` CLI is missing
    error: str | None = None


def load_plugins(project_path: Path) -> PluginsSnapshot:
    """Merge the live marketplace catalog with local install/enable state."""
    cat = marketplace_catalog()
    if cat is None:
        return PluginsSnapshot(
            rows=[], store_readable=True,
            error="Could not reach the marketplace (offline or missing GitLab token).",
        )
    _, catalog = cat
    installed = claude_installed_plugins()
    store_readable = installed is not None
    installed = installed or {}
    active = set(active_governance_plugins(project_path))
    rows = []
    for name, category in sorted(catalog.items()):
        is_gov = category == "governance"
        enabled = (name in active) if is_gov else bool(installed.get(name))
        rows.append(PluginRow(
            name=name,
            category="governance" if is_gov else "skill",
            installed=name in installed,
            enabled=enabled,
        ))
    return PluginsSnapshot(rows=rows, store_readable=store_readable)


def refresh_catalog(project_path: Path) -> tuple[bool, str]:
    names = refresh_governance_catalog(project_path)
    if names is None:
        return False, "Could not fetch the marketplace catalog (check network / GitLab token)."
    return True, f"Governance catalog refreshed: {', '.join(sorted(names)) or '(none)'}"


def install_plugin(project_path: Path, name: str, category: str) -> tuple[bool, str]:
    """Download plugin content, then set its enable bit (mirrors governance/skill install)."""
    if category == "governance":
        configure_governance_guard(project_path)
    ok, msg = _plugin_install(name, project=project_path)
    if not ok:
        return False, msg
    # Governance: downloaded but inactive until an explicit `use`. Skill: enabled immediately.
    _set_plugin_enabled(project_path, name, category != "governance")
    return True, msg or "installed"


def uninstall_plugin(project_path: Path, name: str, category: str) -> tuple[bool, str]:
    _set_plugin_enabled(project_path, name, False)
    ok, msg = _plugin_uninstall(name)
    return ok, msg or ("uninstalled" if ok else "uninstall failed")


def set_plugin_enabled(project_path: Path, name: str, category: str, enabled: bool) -> tuple[bool, str]:
    """Toggle enable/disable. Governance is mutually exclusive: activating one deactivates the rest."""
    if category == "governance" and enabled:
        for gov in governance_catalog_names(project_path):
            _set_plugin_enabled(project_path, gov, gov == name)
        return True, f"activated {name}"
    _set_plugin_enabled(project_path, name, enabled)
    return True, ("enabled" if enabled else "disabled") + f" {name}"


@dataclass
class SessionRow:
    session_id: str
    title: str | None
    date: str | None
    turns: int
    input_tokens: int
    output_tokens: int
    cache_read: int
    cache_write: int
    cost_usd: float
    path: Path


def load_sessions(project_path: Path, limit: int = 0) -> tuple[list[SessionRow], str | None]:
    """Return (sessions newest-first, match_type); ([], None) if no history is found."""
    result = _claude_sessions_dir(project_path)
    if result is None:
        return [], None
    sessions_dir, match_type = result
    files = sorted(sessions_dir.glob("*.jsonl"), key=lambda p: p.stat().st_mtime, reverse=True)
    if limit:
        files = files[:limit]
    rows = []
    for f in files:
        stats = _parse_session_file(f)
        primary_model = next(iter(sorted(stats["models"])), "")
        cost = _estimate_cost(
            stats["input_tokens"], stats["output_tokens"],
            stats["cache_read"], stats["cache_write"], primary_model,
        )
        rows.append(SessionRow(
            session_id=stats["session_id"], title=stats["title"], date=stats["date"],
            turns=stats["turns"], input_tokens=stats["input_tokens"],
            output_tokens=stats["output_tokens"], cache_read=stats["cache_read"],
            cache_write=stats["cache_write"], cost_usd=cost, path=f,
        ))
    return rows, match_type


def load_session_commands(path: Path) -> list[dict]:
    return _parse_session_commands(path)


def fmt_duration(seconds: float) -> str:
    return _fmt_duration(seconds)


def fmt_local_time(ts: str | None) -> str:
    return _fmt_local_time(ts)


@dataclass
class ToolCheck:
    key: str
    name: str
    found: bool
    skipped: bool  # IDE-based agent, no CLI to check


def load_tool_checks() -> list[ToolCheck]:
    checks = [ToolCheck(key="git", name="Git version control", found=check_tool("git"), skipped=False)]
    for key, cfg in AGENT_CONFIG.items():
        if cfg["requires_cli"]:
            checks.append(ToolCheck(key=key, name=cfg["name"], found=check_tool(key), skipped=False))
        else:
            checks.append(ToolCheck(key=key, name=cfg["name"], found=False, skipped=True))
    return checks


def load_version_info() -> dict:
    return {
        "cli_version": _pandawa_version_str(),
        "has_gitlab_token": _gitlab_token() is not None,
    }


def active_governance(project_path: Path) -> list[str]:
    return active_governance_plugins(project_path)


@dataclass
class ProfileRow:
    key: str
    name: str
    description: str
    version: "str | None"     # None => catalog cache predates the `version` field
    local_path: "str | None"  # None => downloads from GitLab on `pandawa init`


def load_profiles() -> list[ProfileRow]:
    """Domain profiles known to this machine (best-effort refresh from `main` first)."""
    _auto_refresh_profile_catalog()
    config = _effective_profile_config()
    rows = []
    for key, cfg in config.items():
        local = _get_profile_local_path(key)
        rows.append(ProfileRow(
            key=key,
            name=cfg.get("name", key),
            description=cfg.get("description", ""),
            version=cfg.get("version"),
            local_path=str(local) if local else None,
        ))
    return rows


@dataclass
class ProfileStatusRow:
    key: str
    installed_version: "str | None"
    latest_version: "str | None"
    status: str  # "local" | "unknown" | "update_available" | "ahead" | "up_to_date"
    source: "str | None"  # local source path, only set when status == "local"


def load_profile_status(project_path: Path) -> list[ProfileStatusRow]:
    """This project's installed profile(s) (`.pandawa/profile-lock.json`) vs. the live catalog.
    Empty list means no profile is installed in this project — not an error."""
    _auto_refresh_profile_catalog()
    return [
        ProfileStatusRow(
            key=row["id"], installed_version=row["installed_version"],
            latest_version=row["latest_version"], status=row["status"], source=row["source"],
        )
        for row in _profile_status_rows(project_path)
    ]


def refresh_profiles() -> tuple[bool, str]:
    before = set(_effective_profile_config().keys())
    profiles = refresh_profile_catalog()
    if profiles is None:
        return False, "Could not fetch the profile catalog (check network / GitLab token)."
    after = {p["id"] for p in profiles}
    added, removed = sorted(after - before), sorted(before - after)
    msg = f"Profile catalog refreshed. Profiles: {', '.join(sorted(after)) or '(none)'}"
    if added:
        msg += f" | + added: {', '.join(added)}"
    if removed:
        msg += f" | - removed: {', '.join(removed)}"
    return True, msg


def list_agents() -> list[tuple[str, str]]:
    """(key, display name) for every AI assistant `init` knows about."""
    return [(key, cfg["name"]) for key, cfg in AGENT_CONFIG.items()]


def list_script_types() -> list[tuple[str, str]]:
    return list(SCRIPT_TYPE_CHOICES.items())


def default_script_type() -> str:
    return "ps" if os.name == "nt" else "sh"


@dataclass
class InitOptions:
    ai_assistant: str = "claude"
    script_type: "str | None" = None  # None => default_script_type()
    profile_key: "str | None" = None  # None => no profile
    gitlab_token: "str | None" = None  # None => env/saved token (_gitlab_token)
    ignore_agent_tools: bool = False
    no_git: bool = False
    no_marketplace: bool = False
    no_guardrails: bool = False
    no_claude_md: bool = False


def validate_init_options(opts: InitOptions) -> "str | None":
    """Fast, synchronous precheck — return an error message, or None if OK to proceed."""
    if opts.ai_assistant not in AGENT_CONFIG:
        return f"Unknown AI assistant '{opts.ai_assistant}'."
    if not opts.ignore_agent_tools:
        cfg = AGENT_CONFIG[opts.ai_assistant]
        if cfg["requires_cli"] and not check_tool(opts.ai_assistant):
            return (f"{cfg['name']} CLI not found on PATH. Install it first "
                     "(see pandawa check), or enable 'skip agent-tool check'.")
    return None


def init_project_here(project_path: Path, opts: InitOptions, tracker: StepTracker) -> tuple[bool, str]:
    """Scaffold a Pandawa project into `project_path` (always `--here --force` semantics —
    every other TUI tab already operates on this one fixed project_path).

    Mirrors the `init` command's step sequence and conditions exactly, driven by `tracker`
    instead of printing. Call validate_init_options() first; run this off the UI thread —
    it downloads and extracts a real template archive (and profile archive, if selected).
    """
    script_type = opts.script_type or default_script_type()
    gitlab_token = _gitlab_token(opts.gitlab_token)
    is_claude = opts.ai_assistant == "claude"
    tracker.add("final", "Finalize")

    try:
        download_and_extract_template(
            project_path, opts.ai_assistant, script_type, True,
            verbose=False, tracker=tracker, client=_get_client(), gitlab_token=gitlab_token,
        )
        ensure_executable_scripts(project_path, tracker=tracker)

        if is_claude and not opts.no_marketplace:
            tracker.start("marketplace")
            configure_marketplace(project_path, url=DEFAULT_MARKETPLACE_URL,
                                   plugins=MARKETPLACE_BASELINE_PLUGINS, tracker=tracker)
        else:
            tracker.add("marketplace", "Register plugin marketplace")
            tracker.skip("marketplace", "claude only" if not is_claude else "skipped")

        if is_claude and not opts.no_guardrails:
            tracker.start("guardrails")
            configure_guardrails(project_path, deny_rules=BASELINE_DENY_RULES, tracker=tracker)
        else:
            tracker.add("guardrails", "Write baseline guardrails")
            tracker.skip("guardrails", "claude only" if not is_claude else "skipped")

        if is_claude and not opts.no_marketplace:
            tracker.start("governance")
            try:
                refresh_governance_catalog(project_path, url=DEFAULT_MARKETPLACE_URL,
                                            cli_token=gitlab_token, client=_get_client())
            except Exception:
                pass
            configure_governance_guard(project_path, tracker=tracker)
        else:
            tracker.add("governance", "Install governance guard")
            tracker.skip("governance", "claude only" if not is_claude else "skipped")

        if not opts.no_claude_md:
            scaffold_project_context(project_path, tracker=tracker)
        else:
            tracker.add("context", "Scaffold CLAUDE.md")
            tracker.skip("context", "skipped")

        if opts.profile_key:
            local_profile_path = _get_profile_local_path(opts.profile_key)
            download_and_extract_profile(
                project_path, opts.profile_key, opts.ai_assistant,
                local_path=local_profile_path, verbose=False, tracker=tracker,
                client=_get_client(), gitlab_token=gitlab_token,
            )
        else:
            tracker.add("profile-fetch", "Install domain profile")
            tracker.skip("profile-fetch", "no profile selected")

        if not opts.no_git:
            tracker.add("git", "Initialize git repository")
            tracker.start("git")
            if is_git_repo(project_path):
                tracker.complete("git", "existing repo detected")
            elif check_tool("git"):
                success, error_msg = init_git_repo(project_path, quiet=True)
                if success:
                    tracker.complete("git", "initialized")
                else:
                    tracker.error("git", error_msg or "init failed")
            else:
                tracker.skip("git", "git not available")
        else:
            tracker.add("git", "Initialize git repository")
            tracker.skip("git", "skipped")

        tracker.complete("final", "project ready")
        return True, "Project ready."
    except Exception as e:
        tracker.error("final", str(e))
        return False, f"Initialization failed: {e}"


def list_skills() -> list[tuple[str, str]]:
    """(skill key, /pandawa.* slash command) for every `pandawa run <skill>` target."""
    return list(_PANDAWA_SKILLS.items())


@dataclass
class RunResult:
    text: str
    usage: "dict | None"
    model_usage: "dict | None"
    total_cost_usd: "float | None"
    is_error: bool


def run_skill(skill_key: str, goal: str = "", timeout: int = 600) -> RunResult:
    """One-shot, non-interactive: `claude --print --output-format json '<skill> <goal>'`.
    Not a chat session — returns once Claude finishes, with result text + token usage."""
    skill_cmd = _PANDAWA_SKILLS[skill_key]
    text, usage, model_usage, total_cost, is_error = _run_claude_ai(skill_cmd, goal, timeout=timeout)
    return RunResult(text=text, usage=usage, model_usage=model_usage,
                      total_cost_usd=total_cost, is_error=is_error)


_PANDAWA_REPO_URL = "https://git.neuron.id/research/pandawa.git"
_PANDAWA_UPGRADE_COMMAND = ["uv", "tool", "install", "pandawa-cli", "--force",
                          "--from", "git+https://git.neuron.id/research/pandawa.git"]


@dataclass
class VersionCheck:
    current: str
    latest: "str | None"       # None => check failed (offline, no token, bad response)
    update_available: bool


def check_for_update() -> VersionCheck:
    """Compare the installed pandawa-cli package version against pyproject.toml on the pandawa
    repo's `main` branch — the same source `uv tool install --from git+...` would install
    from. NOTE: this is deliberately NOT the GitLab "releases" API the `version` command
    also queries — that tracks TEMPLATE releases (a separate versioning stream, e.g. v0.0.x)
    and is unrelated to the pandawa-cli package version (e.g. 0.22.0); comparing the two would
    misreport an update as available (or missing) essentially at random.
    Non-blocking: uses `_gitlab_auth_headers()` (empty headers if no token), never prompts."""
    current = _pandawa_version_str()
    try:
        api_url = _marketplace_raw_file_url(_PANDAWA_REPO_URL, file_path="pyproject.toml", ref="main")
        if not api_url:
            return VersionCheck(current=current, latest=None, update_available=False)
        resp = _get_client().get(api_url, timeout=10, follow_redirects=True, headers=_gitlab_auth_headers())
        if resp.status_code != 200:
            return VersionCheck(current=current, latest=None, update_available=False)
        import tomllib
        latest = tomllib.loads(resp.text).get("project", {}).get("version")
        update_available = bool(latest) and latest != current
        return VersionCheck(current=current, latest=latest, update_available=update_available)
    except Exception:
        return VersionCheck(current=current, latest=None, update_available=False)


def upgrade_cli(timeout: int = 180) -> tuple[bool, str]:
    """Run `uv tool install pandawa-cli --force --from git+...` (docs/upgrade.md's "CLI Tool
    Only" path). Requires `uv` on PATH and that pandawa was installed via `uv tool install` —
    other install methods (pip, pipx, source checkout) need their own upgrade path, so this
    fails gracefully rather than guessing. Cannot hot-swap the currently running process —
    caller must tell the user to restart `pandawa`/`pandawa tui` after a successful upgrade."""
    if shutil.which("uv") is None:
        return False, "`uv` not found on PATH — see docs/upgrade.md for other install methods."
    try:
        p = subprocess.run(_PANDAWA_UPGRADE_COMMAND, capture_output=True, text=True, timeout=timeout)
    except Exception as e:
        return False, str(e)
    if p.returncode != 0:
        return False, (p.stderr or p.stdout or f"`uv tool install` failed (exit {p.returncode}).").strip()
    return True, "Updated. Restart pandawa (or pandawa tui) to use the new version."
