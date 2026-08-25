"""Role agent contract: valid frontmatter, phases, and resolvable skill refs."""

import re
from pathlib import Path

AGENTS_DIR = Path(__file__).resolve().parent.parent / "agents"
SKILLS_DIR = Path(__file__).resolve().parent.parent / "skills"
FM_RE = re.compile(r'\A---\n(.*?)\n---\n', re.DOTALL)


def test_role_files_valid():
    roles = sorted(p for p in AGENTS_DIR.glob("*.md") if p.name != "README.md")
    assert len(roles) == 5, f"expected 5 Pandawa roles, found {[r.name for r in roles]}"
    phases = set()
    for path in roles:
        text = path.read_text(encoding="utf-8")
        m = FM_RE.match(text)
        assert m, f"{path.name}: missing frontmatter"
        fm = m.group(1)
        phase = re.search(r"phase: (\S+)", fm)
        assert phase, f"{path.name}: missing phase"
        phases.add(phase.group(1))
        for skill in re.findall(r'"([a-z0-9-]+)"', re.search(r"skills: \[(.*?)\]", fm).group(1)):
            assert (SKILLS_DIR / skill / "SKILL.md").exists(), (
                f"{path.name}: references unknown skill '{skill}'"
            )
    assert phases == {"plan", "implement", "review", "verify"}
