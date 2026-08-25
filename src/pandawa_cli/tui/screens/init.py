"""Init pane: scaffold this project directory (always `--here --force` semantics —
every other tab already operates on the one fixed project_path, so Init does too).
"""
from __future__ import annotations

from pathlib import Path

from textual import work
from textual.app import ComposeResult
from textual.containers import Vertical, VerticalScroll
from textual.widgets import Button, Checkbox, Input, Select, Static

from .. import data


class InitPane(Vertical):
    def __init__(self, project_path: Path) -> None:
        super().__init__()
        self.project_path = project_path
        self._busy = False
        self._tracker: "data.StepTracker | None" = None

    def compose(self) -> ComposeResult:
        with VerticalScroll():
            yield Static(
                f"[yellow]This merges the Pandawa template into[/yellow] [cyan]{self.project_path}[/cyan]"
                f"[yellow]. Existing files may be overwritten.[/yellow]",
                id="init-warning",
            )
            yield Static("AI assistant", classes="init-label")
            yield Select(
                [(name, key) for key, name in data.list_agents()],
                value="claude", id="init-agent",
            )
            yield Static("Script type", classes="init-label")
            yield Select(
                [(name, key) for key, name in data.list_script_types()],
                value=data.default_script_type(), id="init-script",
            )
            yield Static("Domain profile", classes="init-label")
            yield Select([("No profile", "none")], value="none", id="init-profile")
            yield Static("GitLab token override (blank = use saved/env token)", classes="init-label")
            yield Input(placeholder="glpat-…", password=True, id="init-token")
            yield Checkbox("Skip agent-tool check (--ignore-agent-tools)", id="init-ignore-agent-tools")
            yield Checkbox("Skip git init (--no-git)", id="init-no-git")
            yield Checkbox("Skip marketplace registration, claude only (--no-marketplace)", id="init-no-marketplace")
            yield Checkbox("Skip baseline guardrails, claude only (--no-guardrails)", id="init-no-guardrails")
            yield Checkbox("Skip CLAUDE.md scaffold (--no-claude-md)", id="init-no-claude-md")
            yield Button("Initialize project here", variant="primary", id="init-submit")
            yield Static("", id="init-status")
            yield Static("", id="init-progress")

    def on_mount(self) -> None:
        self._load_profile_options()

    @work(thread=True, exclusive=True)
    def _load_profile_options(self) -> None:
        rows = data.load_profiles()
        self.app.call_from_thread(self._apply_profile_options, rows)

    def _apply_profile_options(self, rows: list[data.ProfileRow]) -> None:
        options = [("No profile", "none")] + [(f"{r.name} ({r.key})", r.key) for r in rows]
        select = self.query_one("#init-profile", Select)
        current = select.value
        select.set_options(options)
        # set_options() resets the selection; restore it (still valid, since "No profile"/
        # "none" and every previously-listed profile key are always re-included above).
        select.value = current if current is not Select.BLANK else "none"

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "init-submit":
            self._submit()

    def _set_status(self, message: str, *, error: bool = False) -> None:
        style = "red" if error else "green"
        self.query_one("#init-status", Static).update(f"[{style}]{message}[/{style}]")

    def _submit(self) -> None:
        if self._busy:
            return
        agent_value = self.query_one("#init-agent", Select).value
        script_value = self.query_one("#init-script", Select).value
        profile_value = self.query_one("#init-profile", Select).value
        token_value = self.query_one("#init-token", Input).value.strip()

        opts = data.InitOptions(
            ai_assistant=str(agent_value),
            script_type=str(script_value) if script_value else None,
            profile_key=None if profile_value in (None, "none") else str(profile_value),
            gitlab_token=token_value or None,
            ignore_agent_tools=self.query_one("#init-ignore-agent-tools", Checkbox).value,
            no_git=self.query_one("#init-no-git", Checkbox).value,
            no_marketplace=self.query_one("#init-no-marketplace", Checkbox).value,
            no_guardrails=self.query_one("#init-no-guardrails", Checkbox).value,
            no_claude_md=self.query_one("#init-no-claude-md", Checkbox).value,
        )
        error = data.validate_init_options(opts)
        if error:
            self._set_status(error, error=True)
            return

        self._busy = True
        self.query_one("#init-submit", Button).disabled = True
        self._set_status("Initializing…")
        self._tracker = data.StepTracker("Initialize Pandawa Project")
        self._tracker.attach_refresh(lambda: self.app.call_from_thread(self._render_tracker))
        self._render_tracker()
        self._do_init(opts)

    def _render_tracker(self) -> None:
        if self._tracker is not None:
            self.query_one("#init-progress", Static).update(self._tracker.render())

    @work(thread=True, exclusive=True)
    def _do_init(self, opts: "data.InitOptions") -> None:
        ok, msg = data.init_project_here(self.project_path, opts, self._tracker)
        self.app.call_from_thread(self._after_init, ok, msg)

    def _after_init(self, ok: bool, msg: str) -> None:
        self._busy = False
        self.query_one("#init-submit", Button).disabled = False
        self._render_tracker()
        self._set_status(msg, error=not ok)
        if ok:
            self.app.refresh_all()
