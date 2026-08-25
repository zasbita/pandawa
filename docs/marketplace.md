<div align="center">
    <img src="/media/logo_large.png" alt="Pandawa Logo" width="200" height="200"/>
</div>

# Marketplace: Plugins & Domain Profiles

Pandawa ships two kinds of extension content through a private GitLab marketplace —
**skill/agent plugins** and **domain profiles**. Both are contributed, reviewed, and
validated in one dedicated repo, separate from this one: **`pandawa-marketplace-tooling`**
(`https://git.neuron.id/research/pandawa-marketplace-tooling.git`). This page is the
one-stop pointer for both *using* and *contributing to* that marketplace — the
[README](https://git.neuron.id/research/pandawa/blob/main/README.md) and
[PANDUAN.md](https://git.neuron.id/research/pandawa/blob/main/PANDUAN.md) cover day-to-day
usage in depth already; this page exists so anyone opening this repo also learns the
marketplace exists and how to add to it.

## The two content types

| | **Plugin** (`plugins/`) | **Domain Profile** (`profiles/`) |
|---|---|---|
| Contains | Claude Code skills and/or agents | Constitution/architecture/standards overlay for one domain (e.g. TM Forum ODA) |
| Installed via | Claude Code's native `/plugin install <name>@pandawa` | `pandawa init --profile <id>` / `pandawa profile` (the `pandawa` CLI itself) |
| Works on | **Claude Code only** | **Every agent `pandawa` supports** (Gemini, Cursor, Copilot, and more) |
| Content delivery | Claude Code `git clone`/`pull`s the marketplace repo | `pandawa` fetches the profile's folder live via GitLab's archive API — no clone, no release |
| Versioning | `version` in `plugin.json`, consumers opt into updates | `version` in `profile.json` too, but **not** a pin — `pandawa init --profile`/`pandawa profile update` always fetch current `main`. A per-project lockfile (`.pandawa/profile-lock.json`) records what's installed, and `pandawa profile status` diffs it against the catalog to surface "update available" |

See the [README's Domain Profiles section](https://git.neuron.id/research/pandawa/blob/main/README.md#domain-profiles)
for the consumer-facing `pandawa profile`/`pandawa skill`/`pandawa governance` commands, and
[PANDUAN.md](https://git.neuron.id/research/pandawa/blob/main/PANDUAN.md) for the guided
terminal + Claude Code walkthrough.

## Contributing

Anyone in the company can contribute a new skill, agent, or domain profile — there is
no code change or release needed in **this** repo (`pandawa`) for either. Short version:

1. Clone `pandawa-marketplace-tooling`.
2. Decide which kind you're adding:
   - A capability Claude actively invokes, or a sub-agent → add it under `plugins/<name>/`.
   - Domain knowledge/standards other agents should read before generating code in a
     domain → add it under `profiles/<id>/` and register it in that repo's `profiles.json`.
3. Run `python tools/validate-marketplace.py .` there before opening a merge request.
4. Open the MR — CI re-runs the same validator, and the folder's owner (see that repo's
   `CODEOWNERS`) reviews it. A profile is live for everyone via `pandawa init --profile`
   the moment it merges to `main`; a plugin becomes installable via `/plugin install`.

**Full walkthrough, including the complete domain-profile folder anatomy, local
testing before opening an MR, and the CODEOWNERS/versioning rules**, is written up
end-to-end in that repo's own docs — start there rather than duplicating it here:

- [`pandawa-marketplace-tooling/docs/PANDUAN-KOLABORASI.md`](https://git.neuron.id/research/pandawa-marketplace-tooling/blob/main/docs/PANDUAN-KOLABORASI.md) — full start-to-finish collaboration guide (Bahasa Indonesia), including detailed domain-profile rules.
- [`pandawa-marketplace-tooling/CONTRIBUTING.md`](https://git.neuron.id/research/pandawa-marketplace-tooling/blob/main/CONTRIBUTING.md) — terse technical reference.
- [`pandawa-marketplace-tooling/README.md`](https://git.neuron.id/research/pandawa-marketplace-tooling/blob/main/README.md) — concepts and consumer usage.

## See also

- [Roadmap — Phase 3](https://git.neuron.id/research/pandawa/blob/main/docs/roadmap.md) discusses where the marketplace is headed (package catalog, trust/governance layer, compatibility matrix).
- [Cross-Agent UX Consistency](cross-agent-consistency.md) explains why marketplace plugin delivery is Claude-only today, and the open problem of extending it cross-agent.
