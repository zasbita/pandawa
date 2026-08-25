"""install_layers: bundled skills/agents land in .pandawa and native host dirs."""

from pathlib import Path

from pandawa_cli import install_layers


def _project(tmp_path: Path) -> Path:
    p = tmp_path / "proj"
    p.mkdir()
    return p


def test_layers_installed_all_hosts(tmp_path):
    proj = _project(tmp_path)
    install_layers(proj, "gemini")
    assert (proj / ".pandawa" / "skills" / "brainstorming" / "SKILL.md").is_file()
    assert (proj / ".pandawa" / "agents" / "bima-builder.md").is_file()
    assert not (proj / ".claude").exists(), "no native dir copy for unsupported host"


def test_layers_native_copy_for_claude(tmp_path):
    proj = _project(tmp_path)
    install_layers(proj, "claude")
    assert (proj / ".claude" / "skills" / "brainstorming" / "SKILL.md").is_file()
    assert (proj / ".claude" / "skills" / "code-review" / "SKILL.md").is_file()


def test_layers_missing_source_skips(tmp_path, monkeypatch):
    monkeypatch.setenv("PANDAWA_HOME", str(tmp_path / "nowhere"))
    proj = _project(tmp_path)
    install_layers(proj, "claude")  # must not raise
    assert not (proj / ".pandawa").exists()
