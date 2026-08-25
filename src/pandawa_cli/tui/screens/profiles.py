"""Profiles pane: browse domain profiles known to this machine, refresh the catalog.

Read-only besides refresh — `pandawa profile set-local` (pointing a profile at a local
directory for testing) stays CLI-only; it's a dev/debug affordance, not day-to-day use.
This pane is catalog-level (which profiles exist, machine-wide) and mirrors `pandawa profile
list`; whether the CURRENT project has one installed and up to date is shown on the Status
tab instead (project-scoped, mirrors `pandawa profile status`).
"""
from __future__ import annotations

from textual import work
from textual.app import ComposeResult
from textual.binding import Binding
from textual.containers import Vertical
from textual.widgets import DataTable, Static

from .. import data


class ProfilesPane(Vertical):
    BINDINGS = [Binding("r", "refresh", "Refresh catalog")]

    def __init__(self) -> None:
        super().__init__()
        self._busy = False

    def compose(self) -> ComposeResult:
        yield Static("Loading profiles…", id="profiles-status")
        yield DataTable(id="profiles-table", zebra_stripes=True, cursor_type="row")

    def on_mount(self) -> None:
        table = self.query_one("#profiles-table", DataTable)
        table.add_columns("Key", "Name", "Version", "Local path")
        self.load_profiles()

    @work(thread=True, exclusive=True)
    def load_profiles(self) -> None:
        rows = data.load_profiles()
        self.app.call_from_thread(self._apply, rows)

    def _apply(self, rows: list[data.ProfileRow]) -> None:
        table = self.query_one("#profiles-table", DataTable)
        table.clear()
        for row in rows:
            path_str = row.local_path or "[dim]— (download from GitLab)[/dim]"
            table.add_row(row.key, row.name, row.version or "[dim]—[/dim]", path_str)
        self._set_status(
            f"{len(rows)} profiles. r refresh catalog · "
            "use `pandawa profile status`/`update` in the CLI to check an installed project for updates."
        )

    def action_refresh(self) -> None:
        if self._busy:
            return
        self._busy = True
        self._set_status("Refreshing profile catalog…")
        self._do_refresh()

    @work(thread=True, exclusive=True)
    def _do_refresh(self) -> None:
        ok, msg = data.refresh_profiles()
        self.app.call_from_thread(self._after_refresh, ok, msg)

    def _after_refresh(self, ok: bool, msg: str) -> None:
        self._busy = False
        self._set_status(msg, error=not ok)
        self.load_profiles()

    def _set_status(self, message: str, *, error: bool = False) -> None:
        style = "red" if error else "green"
        self.query_one("#profiles-status", Static).update(f"[{style}]{message}[/{style}]")
