"""Usage pane: session history and cost, drilling into per-/pandawa.* command breakdown."""
from __future__ import annotations

from pathlib import Path

from textual import work
from textual.app import ComposeResult
from textual.containers import Vertical
from textual.widgets import DataTable, Static

from .. import data


class UsagePane(Vertical):
    def __init__(self, project_path: Path) -> None:
        super().__init__()
        self.project_path = project_path
        self._sessions: list[data.SessionRow] = []

    def compose(self) -> ComposeResult:
        yield Static("Loading usage…", id="usage-summary")
        yield DataTable(id="usage-sessions", zebra_stripes=True, cursor_type="row")
        yield Static("Commands in selected session", id="usage-commands-label")
        yield DataTable(id="usage-commands", zebra_stripes=True, cursor_type="row")

    def on_mount(self) -> None:
        sessions = self.query_one("#usage-sessions", DataTable)
        sessions.add_columns("Date", "Title", "Turns", "In", "Out", "Cache R", "Cache W", "Cost ($)")
        commands = self.query_one("#usage-commands", DataTable)
        commands.add_columns("Command", "Start", "Duration", "Turns", "In", "Out", "Cost ($)")
        self.load_sessions()

    @work(thread=True, exclusive=True)
    def load_sessions(self) -> None:
        sessions, match_type = data.load_sessions(self.project_path, limit=50)
        self.app.call_from_thread(self._apply_sessions, sessions, match_type)

    def _apply_sessions(self, sessions: list[data.SessionRow], match_type: "str | None") -> None:
        self._sessions = sessions
        table = self.query_one("#usage-sessions", DataTable)
        table.clear()
        summary = self.query_one("#usage-summary", Static)
        if not sessions:
            summary.update(f"No Claude Code session history found for [cyan]{self.project_path}[/cyan].")
            return
        total_cost = sum(s.cost_usd for s in sessions)
        total_turns = sum(s.turns for s in sessions)
        note = "" if match_type == "exact" else f" [dim](matched via {match_type})[/dim]"
        summary.update(f"{len(sessions)} sessions{note} · {total_turns} turns · est. cost ${total_cost:.2f}")
        for s in sessions:
            table.add_row(
                s.date or "—", s.title or s.session_id[:8], str(s.turns),
                f"{s.input_tokens:,}", f"{s.output_tokens:,}",
                f"{s.cache_read:,}", f"{s.cache_write:,}", f"{s.cost_usd:.3f}",
            )

    def on_data_table_row_highlighted(self, event: DataTable.RowHighlighted) -> None:
        if event.data_table.id != "usage-sessions":
            return
        idx = event.cursor_row
        if 0 <= idx < len(self._sessions):
            self._load_commands(self._sessions[idx].path)

    @work(thread=True, exclusive=True)
    def _load_commands(self, path: Path) -> None:
        commands = data.load_session_commands(path)
        self.app.call_from_thread(self._apply_commands, commands)

    def _apply_commands(self, commands: list[dict]) -> None:
        table = self.query_one("#usage-commands", DataTable)
        table.clear()
        label = self.query_one("#usage-commands-label", Static)
        if not commands:
            label.update("Commands in selected session — [dim]none found[/dim]")
            return
        label.update(f"Commands in selected session — {len(commands)}")
        for c in commands:
            table.add_row(
                c["command"],
                data.fmt_local_time(c["start_ts"]),
                data.fmt_duration(c["duration_s"]),
                str(c["turns"]),
                f"{c['input_tokens']:,}",
                f"{c['output_tokens']:,}",
                f"{c['cost_usd']:.3f}",
            )
