#!/usr/bin/env python3
"""Import superpowers skills into the Pandawa unified skill registry.

Re-runnable: re-syncs from a superpowers checkout, preserving any manual
edits is NOT attempted (upstream wins). Phase mapping lives in PHASES.
"""

from __future__ import annotations

import shutil
import sys
from pathlib import Path

SRC = Path(sys.argv[1]) if len(sys.argv) > 1 else Path(r"C:\work\ristek\superpowers\skills")
DST = Path(__file__).resolve().parent.parent / "skills"

PHASES = {
    "brainstorming": "plan",
    "writing-plans": "plan",
    "executing-plans": "implement",
    "subagent-driven-development": "implement",
    "dispatching-parallel-agents": "tasks",
    "test-driven-development": "implement",
    "verification-before-completion": "verify",
    "systematic-debugging": "implement",
    "requesting-code-review": "review",
    "receiving-code-review": "review",
    "finishing-a-development-branch": "review",
    "using-git-worktrees": "tasks",
    "using-superpowers": "constitution",
    "writing-skills": "constitution",
}


def parse_frontmatter(text: str) -> tuple[dict, str]:
    if not text.startswith("---"):
        return {}, text
    _, fm, body = text.split("---", 2)
    meta: dict[str, str] = {}
    for line in fm.strip().splitlines():
        if ":" in line:
            k, v = line.split(":", 1)
            meta[k.strip()] = v.strip().strip('"')
    return meta, "---" + body


def render(name: str, description: str, phase: str, body: str) -> str:
    return (
        "---\n"
        f'name: "{name}"\n'
        f'description: "{description}"\n'
        f"phase: {phase}\n"
        "source: superpowers\n"
        f'aliases: ["superpowers:{name}"]\n'
        "---\n" + body.lstrip("\n")
    )


def main() -> int:
    if not SRC.is_dir():
        print(f"source not found: {SRC}")
        return 1
    imported = 0
    for skill_dir in sorted(SRC.iterdir()):
        skill_md = skill_dir / "SKILL.md"
        if not skill_md.is_file():
            continue
        name = skill_dir.name
        phase = PHASES.get(name)
        if phase is None:
            print(f"skip (no phase mapping): {name}")
            continue
        meta, body = parse_frontmatter(skill_md.read_text(encoding="utf-8"))
        out_dir = DST / name
        if out_dir.exists():
            shutil.rmtree(out_dir)
        shutil.copytree(skill_dir, out_dir)
        (out_dir / "SKILL.md").write_text(
            render(meta.get("name", name), meta.get("description", ""), phase, body),
            encoding="utf-8",
        )
        imported += 1
        print(f"imported: {name} -> phase={phase}")
    print(f"\n{imported} skills imported into {DST}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
