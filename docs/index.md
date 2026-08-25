<div align="center">
    <img src="/media/logo_large.png" alt="Pandawa Logo" width="200" height="200"/>
</div>

# Pandawa

*Build high-quality software faster.*

**An effort to allow organizations to focus on product scenarios rather than writing undifferentiated code with the help of Spec-Driven Development.**

## What is Spec-Driven Development?

Spec-Driven Development **flips the script** on traditional software development. For decades, code has been king — specifications were just scaffolding we built and discarded once the "real work" of coding began. Spec-Driven Development changes this: **specifications become executable**, directly generating working implementations rather than just guiding them.

## Getting Started

- [Installation Guide](installation.md)
- [Quick Start Guide](quickstart.md)
- [Upgrade Guide](upgrade.md)
- [Local Development](local-development.md)
- [Marketplace: Plugins & Domain Profiles](marketplace.md)

## Commands at a Glance

Install with `pandawa init <project-name> --ai <your-agent>`, then drive the workflow from your AI agent's chat using these `/pandawa.*` commands, in order:

| # | Command | What it does |
| - | --- | --- |
| 1 | `/pandawa.constitution` | Establish project governing principles |
| — | `/pandawa.brd` *(existing projects only)* | Reverse-engineer a BRD from the current codebase before specifying |
| 2 | `/pandawa.specify` | Define what to build (requirements, user stories) |
| 3 | `/pandawa.clarify` *(optional)* | Resolve ambiguities in the spec |
| 4 | `/pandawa.plan` | Create a technical implementation plan |
| 5 | `/pandawa.tasks` | Break the plan into actionable tasks |
| 6 | `/pandawa.analyze` *(optional)* | Check spec/plan/tasks for consistency before implementing |
| 7 | `/pandawa.implement` | Execute the tasks and build the feature |
| — | `/pandawa.test` *(optional)* | Generate missing tests, run quality checks, report bugs |
| — | `/pandawa.redesign` *(optional)* | Scoped rework of one already-implemented part |

Prefer one command over the whole sequence? `/pandawa.ultimate <your goal>` runs steps 1–7 for you, pausing for confirmation between each phase. See the [Quick Start Guide](quickstart.md) for a full walkthrough, or the [README's CLI Reference](https://git.neuron.id/research/pandawa/blob/main/README.md#-pandawa-cli-reference) for every `pandawa` CLI subcommand (`init`, `profile`, `check`, `usage`, `governance`, `skill`, `run`).

## Core Philosophy

Spec-Driven Development is a structured process that emphasizes:

- **Intent-driven development** where specifications define the "*what*" before the "*how*"
- **Rich specification creation** using guardrails and organizational principles
- **Multi-step refinement** rather than one-shot code generation from prompts
- **Heavy reliance** on advanced AI model capabilities for specification interpretation

## Development Phases

| Phase | Focus | Key Activities |
| ----- | ----- | -------------- |
| **0-to-1 Development** ("Greenfield") | Generate from scratch | <ul><li>Start with high-level requirements</li><li>Generate specifications</li><li>Plan implementation steps</li><li>Build production-ready applications</li></ul> |
| **Creative Exploration** | Parallel implementations | <ul><li>Explore diverse solutions</li><li>Support multiple technology stacks & architectures</li><li>Experiment with UX patterns</li></ul> |
| **Iterative Enhancement** ("Brownfield") | Brownfield modernization | <ul><li>Add features iteratively</li><li>Modernize legacy systems</li><li>Adapt processes</li></ul> |

## Experimental Goals

Our research and experimentation focus on:

### Technology Independence

- Create applications using diverse technology stacks
- Validate the hypothesis that Spec-Driven Development is a process not tied to specific technologies, programming languages, or frameworks

### Enterprise Constraints

- Demonstrate mission-critical application development
- Incorporate organizational constraints (cloud providers, tech stacks, engineering practices)
- Support enterprise design systems and compliance requirements

### User-Centric Development

- Build applications for different user cohorts and preferences
- Support various development approaches (from vibe-coding to AI-native development)

### Creative & Iterative Processes

- Validate the concept of parallel implementation exploration
- Provide robust iterative feature development workflows
- Extend processes to handle upgrades and modernization tasks

## Contributing

Please see our [Contributing Guide](https://git.neuron.id/research/pandawa/blob/main/CONTRIBUTING.md) for information on how to contribute to this project.

## Support

For support, please check our [Support Guide](https://git.neuron.id/research/pandawa/blob/main/SUPPORT.md) or open an issue on GitHub.
