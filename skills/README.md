# Skills

This directory is the **customization layer** of the demo. Each skill is a
markdown file (plus optional helper scripts/examples) that the agent loads
at runtime to learn how this team works — without changing any agent code.

| Skill | Authored / Vendored | Loaded by | Purpose |
|---|---|---|---|
| [`webapp-testing/`](./webapp-testing/) | Vendored from [anthropics/skills](https://github.com/anthropics/skills/tree/main/skills/webapp-testing) | `ui_qa_agent.py` | Runtime Playwright pattern (reconnaissance-then-action, `with_server.py` helper) |
| [`front-end-testing/`](./front-end-testing/) | Vendored from [citypaul/.dotfiles](https://github.com/citypaul/.dotfiles/blob/main/claude/.claude/skills/front-end-testing/SKILL.md) | `ui_qa_agent.py` | Quality bar for emitted Playwright specs (accessibility-first, idempotency, MSW) |
| [`api-qa-conventions/`](./api-qa-conventions/) | **Authored for this demo** | `api_qa_agent.py` | Pytest + httpx conventions for the API QA agent |

## Why skills instead of agent code

The customer-facing point: **the agent's behavior is configured by markdown
files, not Python.** A QA lead can author or update a skill in their text
editor of choice and the agent picks it up on the next run.

This is what we mean by *customizable*: no Python, no plugin SDK, no
re-deploys — just a markdown file checked into version control.

## How they get loaded

See `agents/api_qa_agent.py` and `agents/ui_qa_agent.py`. Each agent is
constructed with a `skills=[...]` list that points at these directories.
At runtime the OpenHands SDK reads the `SKILL.md` frontmatter and the
agent uses the body as context-relevant guidance.

## Adding a new skill

1. Create a new subdirectory: `skills/<your-skill-name>/`
2. Add a `SKILL.md` with YAML frontmatter:
   ```markdown
   ---
   name: your-skill-name
   description: One-paragraph trigger description — what the skill teaches and when to use it.
   ---

   # Your Skill Name

   ...
   ```
3. Reference it in the appropriate agent's `skills=[...]` list.
