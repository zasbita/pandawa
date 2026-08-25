"""Plugins pane: browse the marketplace catalog, install/uninstall, enable/disable."""
from __future__ import annotations

from pathlib import Path

from textual import work
from textual.app import ComposeResult
from textual.binding import Binding
from textual.containers import Vertical
from textual.widgets import DataTable, Input, Static

from .. import data


class PluginsPane(Vertical):
    BINDINGS = [
        Binding("i", "install", "Install"),
        Binding("u", "uninstall", "Uninstall"),
        Binding("e", "toggle_enabled", "Enable/Disable"),
        Binding("r", "refresh", "Refresh catalog"),
        Binding("/", "focus_filter", "Filter"),
    ]

    def __init__(self, project_path: Path) -> None:
        super().__init__()
        self.project_path = project_path
        self._visible: list[data.PluginRow] = []
        self._filter = ""
        self._busy = False

    def compose(self) -> ComposeResult:
        yield Input(placeholder="Filter by name or category… (press / to focus)", id="plugins-filter")
        yield DataTable(id="plugins-table", zebra_stripes=True, cursor_type="row")
        yield Static("Loading plugins…", id="plugins-status")

    def on_mount(self) -> None:
        table = self.query_one("#plugins-table", DataTable)
        table.add_columns("Name", "Category", "Installed", "Enabled/Active")
        self.load_plugins()

    @work(thread=True, exclusive=True)
    def load_plugins(self) -> None:
        snapshot = data.load_plugins(self.project_path)
        self.app.call_from_thread(self._apply_snapshot, snapshot)

    def _apply_snapshot(self, snapshot: data.PluginsSnapshot) -> None:
        self._all_rows = snapshot.rows
        if snapshot.error:
            self._set_status(snapshot.error, error=True)
        elif not snapshot.store_readable:
            self._set_status("claude CLI not found — install/enable state may be incomplete.", error=True)
        else:
            self._set_status(
                f"{len(self._all_rows)} plugins in marketplace. "
                "i install · u uninstall · e enable/disable · r refresh catalog"
            )
        self._render_rows()

    def _render_rows(self) -> None:
        table = self.query_one("#plugins-table", DataTable)
        table.clear()
        needle = self._filter.strip().lower()
        self._visible = [
            row for row in getattr(self, "_all_rows", [])
            if not needle or needle in row.name.lower() or needle in row.category.lower()
        ]
        for row in self._visible:
            installed = "[green]yes[/green]" if row.installed else "[dim]no[/dim]"
            if row.category == "governance":
                enabled = "[bold green]active[/bold green]" if row.enabled else "[dim]inactive[/dim]"
            else:
                enabled = "[bold green]enabled[/bold green]" if row.enabled else "[dim]disabled[/dim]"
            table.add_row(row.name, row.category, installed, enabled)

    def on_input_changed(self, event: Input.Changed) -> None:
        if event.input.id == "plugins-filter":
            self._filter = event.value
            self._render_rows()

    def action_focus_filter(self) -> None:
        self.query_one("#plugins-filter", Input).focus()

    def _selected_row(self) -> "data.PluginRow | None":
        table = self.query_one("#plugins-table", DataTable)
        if table.row_count == 0 or table.cursor_row is None:
            return None
        if 0 <= table.cursor_row < len(self._visible):
            return self._visible[table.cursor_row]
        return None

    def _set_status(self, message: str, *, error: bool = False) -> None:
        style = "red" if error else "green"
        self.query_one("#plugins-status", Static).update(f"[{style}]{message}[/{style}]")

    def action_install(self) -> None:
        row = self._selected_row()
        if row is None or self._busy:
            return
        if row.installed:
            self._set_status(f"'{row.name}' is already installed.")
            return
        self._busy = True
        self._set_status(f"Installing {row.name}…")
        self._do_install(row.name, row.category)

    @work(thread=True, exclusive=True)
    def _do_install(self, name: str, category: str) -> None:
        ok, msg = data.install_plugin(self.project_path, name, category)
        self.app.call_from_thread(self._after_action, ok, f"Installed {name}." if ok else msg)

    def action_uninstall(self) -> None:
        row = self._selected_row()
        if row is None or self._busy:
            return
        if not row.installed:
            self._set_status(f"'{row.name}' is not installed.")
            return
        self._busy = True
        self._set_status(f"Uninstalling {row.name}…")
        self._do_uninstall(row.name, row.category)

    @work(thread=True, exclusive=True)
    def _do_uninstall(self, name: str, category: str) -> None:
        ok, msg = data.uninstall_plugin(self.project_path, name, category)
        self.app.call_from_thread(self._after_action, ok, f"Removed {name}." if ok else msg)

    def action_toggle_enabled(self) -> None:
        row = self._selected_row()
        if row is None or self._busy:
            return
        if not row.installed:
            self._set_status(f"Install '{row.name}' first.")
            return
        self._busy = True
        target = not row.enabled
        verb = "Activating" if (row.category == "governance" and target) else ("Enabling" if target else "Disabling")
        self._set_status(f"{verb} {row.name}…")
        self._do_toggle(row.name, row.category, target)

    @work(thread=True, exclusive=True)
    def _do_toggle(self, name: str, category: str, enabled: bool) -> None:
        ok, msg = data.set_plugin_enabled(self.project_path, name, category, enabled)
        self.app.call_from_thread(self._after_action, ok, msg)

    def action_refresh(self) -> None:
        if self._busy:
            return
        self._busy = True
        self._set_status("Refreshing marketplace catalog…")
        self._do_refresh()

    @work(thread=True, exclusive=True)
    def _do_refresh(self) -> None:
        ok, msg = data.refresh_catalog(self.project_path)
        self.app.call_from_thread(self._after_action, ok, msg)

    def _after_action(self, ok: bool, msg: str) -> None:
        self._busy = False
        self._set_status(msg, error=not ok)
        self.load_plugins()
