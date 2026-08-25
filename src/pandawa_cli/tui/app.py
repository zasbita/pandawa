"""Main Textual application: tabs for Status, Init, Plugins, Profiles, Usage, and Run."""
from __future__ import annotations

from pathlib import Path

from textual.app import App, ComposeResult
from textual.widgets import Footer, Header, TabbedContent, TabPane

from .screens.init import InitPane
from .screens.plugins import PluginsPane
from .screens.profiles import ProfilesPane
from .screens.run import RunPane
from .screens.status import StatusPane
from .screens.usage import UsagePane


class PandawaTUIApp(App):
    TITLE = "Pandawa"
    CSS_PATH = "styles.tcss"
    BINDINGS = [("q", "quit", "Quit")]

    def __init__(self, project_path: "Path | None" = None) -> None:
        super().__init__()
        self.project_path = project_path or Path.cwd()

    def compose(self) -> ComposeResult:
        yield Header()
        with TabbedContent(initial="status"):
            with TabPane("Status", id="status"):
                yield StatusPane(self.project_path)
            with TabPane("Init", id="init"):
                yield InitPane(self.project_path)
            with TabPane("Plugins", id="plugins"):
                yield PluginsPane(self.project_path)
            with TabPane("Profiles", id="profiles"):
                yield ProfilesPane()
            with TabPane("Usage", id="usage"):
                yield UsagePane(self.project_path)
            with TabPane("Run", id="run"):
                yield RunPane()
        yield Footer()

    def on_mount(self) -> None:
        self.sub_title = str(self.project_path)

    def refresh_all(self) -> None:
        """Reload Status/Plugins/Profiles after an action elsewhere changes project state
        (e.g. a successful Init writes .claude/settings.json and .pandawa/)."""
        self.query_one(StatusPane).load_status()
        self.query_one(PluginsPane).load_plugins()
        self.query_one(ProfilesPane).load_profiles()
