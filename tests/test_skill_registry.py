"""Registry contract: every skill has valid normalized frontmatter."""

import re
from pathlib import Path

SKILLS_DIR = Path(__file__).resolve().parent.parent / "skills"
VALID_PHASES = {"constitution", "plan", "tasks", "implement", "verify", "review"}
VALID_SOURCES = {"superpowers", "gstack", "pandawa"}
FM_RE = re.compile(r'\A---\n(.*?)\n---\n', re.DOTALL)


def test_every_skill_has_valid_frontmatter():
    skills = [d for d in SKILLS_DIR.iterdir() if d.is_dir() and (d / "SKILL.md").exists()]
    assert len(skills) >= 14, "expected the imported superpowers set"
    for d in skills:
        text = (d / "SKILL.md").read_text(encoding="utf-8")
        m = FM_RE.match(text)
        assert m, f"{d.name}: missing frontmatter"
        fm = m.group(1)
        assert f'name: "{d.name}"' in fm, f"{d.name}: bad name"
        assert "description:" in fm, f"{d.name}: missing description"
        phase = re.search(r"phase: (\S+)", fm)
        assert phase and phase.group(1) in VALID_PHASES, f"{d.name}: bad phase"
        source = re.search(r"source: (\S+)", fm)
        assert source and source.group(1) in VALID_SOURCES, f"{d.name}: bad source"
