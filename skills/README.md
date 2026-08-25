# skills/ — Unified Skill Registry

One skill per intent. Format:

```
skills/<skill-name>/
├── SKILL.md        # canonical content (frontmatter: name, description, phase, source)
└── (optional assets)
```

Frontmatter fields: `name`, `description`, `phase` (one of rudis lifecycle phases),
`source` (superpowers | gstack | pandawa), `aliases` (duplicate upstream names).

Populated in Fase 2-3. See docs/architecture.md.
