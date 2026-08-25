"""Run pane: one-shot /pandawa.* skill runner.

`pandawa run <skill> [goal]` is NOT an interactive chat session — it's a single
`claude --print --output-format json` call that returns once Claude finishes,
with result text plus token usage. That makes it a background action like
plugin install, not something that needs a chat UI.
"""
from __future__ import annotations

from rich.text import Text
from textual import work
from textual.app import ComposeResult
from textual.containers import Vertical, VerticalScroll
from textual.widgets import Button, Input, Select, Static

from .. import data


class RunPane(Vertical):
    def __init__(self) -> None:
        super().__init__()
        self._busy = False

    def compose(self) -> ComposeResult:
        yield Static("Skill", classes="run-label")
        yield Select(
            [(cmd, key) for key, cmd in data.list_skills()],
            value="specify", id="run-skill",
        )
        yield Static("Goal / context (optional)", classes="run-label")
        yield Input(placeholder="e.g. focus on the billing module", id="run-goal")
        yield Button("Run", variant="primary", id="run-submit")
        yield Static("", id="run-status")
        with VerticalScroll(id="run-result-scroll"):
            yield Static("", id="run-result")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "run-submit":
            self._submit()

    def _set_status(self, message: str, *, error: bool = False) -> None:
        style = "red" if error else "green"
        self.query_one("#run-status", Static).update(f"[{style}]{message}[/{style}]")

    def _submit(self) -> None:
        if self._busy:
            return
        skill_key = str(self.query_one("#run-skill", Select).value)
        goal = self.query_one("#run-goal", Input).value.strip()
        self._busy = True
        self.query_one("#run-submit", Button).disabled = True
        self.query_one("#run-result", Static).update("")
        self._set_status(f"Running /pandawa.{skill_key}… this can take a while (up to 10 min).")
        self._do_run(skill_key, goal)

    @work(thread=True, exclusive=True)
    def _do_run(self, skill_key: str, goal: str) -> None:
        result = data.run_skill(skill_key, goal)
        self.app.call_from_thread(self._after_run, result)

    def _after_run(self, result: "data.RunResult") -> None:
        self._busy = False
        self.query_one("#run-submit", Button).disabled = False
        self.query_one("#run-result", Static).update(Text(result.text or "(no output)"))
        if result.is_error:
            self._set_status("Run failed.", error=True)
            return
        usage = result.usage or {}
        turns_info = (
            f"in {usage.get('input_tokens', 0):,} · out {usage.get('output_tokens', 0):,} · "
            f"cache read {usage.get('cache_read_input_tokens', 0):,} · "
            f"cost ${result.total_cost_usd:.3f}" if result.total_cost_usd is not None else ""
        )
        self._set_status(f"Done. {turns_info} — check the Usage tab for the full record.")
