"""Status pane: tool availability, pandawa version, active governance — at a glance."""
from __future__ import annotations

from pathlib import Path

from textual import work
from textual.app import ComposeResult
from textual.containers import Horizontal, Vertical
from textual.widgets import Button, DataTable, Static

from .. import data


class StatusPane(Vertical):
    def __init__(self, project_path: Path) -> None:
        super().__init__()
        self.project_path = project_path
        self._busy = False

    def compose(self) -> ComposeResult:
        yield Static("Loading status…", id="status-summary")
        yield DataTable(id="status-tools", zebra_stripes=True, cursor_type="row")
        yield Static("", id="status-profile")
        with Horizontal(id="status-update-row"):
            yield Static("Checking for updates…", id="status-update")
            yield Button("Update", id="status-update-btn", variant="primary", disabled=True)

    def on_mount(self) -> None:
        table = self.query_one("#status-tools", DataTable)
        table.add_columns("Tool", "Status")
        self.load_status()

    @work(thread=True, exclusive=True)
    def load_status(self) -> None:
        checks = data.load_tool_checks()
        version_info = data.load_version_info()
        active = data.active_governance(self.project_path)
        update_check = data.check_for_update()
        profile_status = data.load_profile_status(self.project_path)
        self.app.call_from_thread(self._apply, checks, version_info, active, update_check, profile_status)

    def _apply(self, checks, version_info, active: list[str], update_check: "data.VersionCheck",
               profile_status: "list[data.ProfileStatusRow]") -> None:
        table = self.query_one("#status-tools", DataTable)
        table.clear()
        for c in checks:
            if c.skipped:
                status = "[dim]IDE-based, no CLI check[/dim]"
            elif c.found:
                status = "[green]available[/green]"
            else:
                status = "[red]not found[/red]"
            table.add_row(c.name, status, key=c.key)

        active_str = ", ".join(active) if active else "[dim]none active[/dim]"
        token_str = "[green]configured[/green]" if version_info["has_gitlab_token"] else "[dim]not configured[/dim]"
        summary = (
            f"[bold]pandawa[/bold] v{version_info['cli_version']}   "
            f"Governance: {active_str}   "
            f"GitLab token: {token_str}   "
            f"Project: [cyan]{self.project_path}[/cyan]"
        )
        self.query_one("#status-summary", Static).update(summary)
        self._render_profile_status(profile_status)
        self._render_update_row(update_check)

    def _render_profile_status(self, rows: "list[data.ProfileStatusRow]") -> None:
        widget = self.query_one("#status-profile", Static)
        if not rows:
            widget.update("[dim]Domain profile: none installed in this project.[/dim]")
            return
        lines = []
        for r in rows:
            version_str = r.installed_version or "?"
            if r.status == "local":
                lines.append(f"[dim]Domain profile: {r.key} v{version_str} "
                              f"(local source — not compared to the catalog)[/dim]")
            elif r.status == "update_available":
                lines.append(f"[yellow]Domain profile: {r.key} v{version_str} — "
                              f"update available (v{r.latest_version})[/yellow] "
                              "— run `pandawa profile update` in a terminal")
            elif r.status == "unknown":
                lines.append(f"[dim]Domain profile: {r.key} v{version_str} "
                              f"(run `pandawa profile refresh` to compare)[/dim]")
            elif r.status == "ahead":
                lines.append(f"[dim]Domain profile: {r.key} v{version_str} "
                              f"(ahead of catalog v{r.latest_version})[/dim]")
            else:
                lines.append(f"[green]Domain profile: {r.key} v{version_str} — up to date[/green]")
        widget.update("\n".join(lines))

    def _render_update_row(self, update_check: "data.VersionCheck") -> None:
        label = self.query_one("#status-update", Static)
        btn = self.query_one("#status-update-btn", Button)
        if update_check.latest is None:
            label.update("[dim]Could not check for updates (offline or unreachable).[/dim]")
            btn.disabled = True
            btn.label = "Update"
        elif update_check.update_available:
            label.update(
                f"[yellow]Update available:[/yellow] v{update_check.latest} "
                f"(you have v{update_check.current})"
            )
            btn.disabled = False
            btn.label = f"Update to v{update_check.latest}"
        else:
            label.update(f"[green]Up to date[/green] (v{update_check.current})")
            btn.disabled = True
            btn.label = "Update"

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "status-update-btn":
            self._start_upgrade()

    def _start_upgrade(self) -> None:
        if self._busy:
            return
        self._busy = True
        self.query_one("#status-update-btn", Button).disabled = True
        self.query_one("#status-update", Static).update("[cyan]Updating… this can take a moment.[/cyan]")
        self._run_upgrade()

    @work(thread=True, exclusive=True)
    def _run_upgrade(self) -> None:
        ok, msg = data.upgrade_cli()
        self.app.call_from_thread(self._after_upgrade, ok, msg)

    def _after_upgrade(self, ok: bool, msg: str) -> None:
        self._busy = False
        style = "green" if ok else "red"
        self.query_one("#status-update", Static).update(f"[{style}]{msg}[/{style}]")
        btn = self.query_one("#status-update-btn", Button)
        if ok:
            btn.label = "Update"
            btn.disabled = True
        else:
            # leave it retryable — restore the label/enabled state the last check produced
            btn.disabled = False
