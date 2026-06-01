# Skills

This directory is the **customization layer** of the demo. Each skill is a
markdown file (plus optional helper scripts/examples) that the agent loads
at runtime to learn how this team works — without changing any agent code.

| Skill | Authored / Vendored | Loaded by | Purpose |
|---|---|---|---|
| [`webapp-testing/`](./webapp-testing/) | Vendored from [anthropics/skills](https://github.com/anthropics/skills/tree/main/skills/webapp-testing) | OpenHands Automation (UI scenario) | Runtime Playwright pattern (reconnaissance-then-action, `with_server.py` helper) |
| [`front-end-testing/`](./front-end-testing/) | Vendored from [citypaul/.dotfiles](https://github.com/citypaul/.dotfiles/blob/main/claude/.claude/skills/front-end-testing/SKILL.md) | OpenHands Automation (UI scenario) | Quality bar for emitted Playwright specs (accessibility-first, idempotency, MSW) |
| [`api-qa-conventions/`](./api-qa-conventions/) | **Authored for this demo** | OpenHands Automation (API scenarios) | Pytest + httpx conventions for the API QA agent |

## Why skills instead of agent code

The customer-facing point: **the agent's behavior is configured by markdown
files, not Python.** A QA lead can author or update a skill in their text
editor of choice and the agent picks it up on the next run.

This is what we mean by *customizable*: no Python, no plugin SDK, no
re-deploys — just a markdown file checked into version control.

## How they get loaded

The OpenHands Automation clones this repo into its sandbox before running.
`AGENTS.md` at the repo root tells the sandbox to auto-load the skills in
this directory. The agent reads `SKILL.md` from each skill folder and uses
the contents as context-relevant guidance for the current task.

## Adding a new skill

1. Create a new subdirectory: `skills/<your-skill-name>/`
2. Add a `SKILL.md` with a clear heading and instructions.
3. Reference it in `AGENTS.md` so the sandbox auto-loads it.
