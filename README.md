# Automated QA Demo

**Land a PR → automated QA runs against your changes → results posted back to the PR.**

For both APIs and UIs. No glue code to write. The agent reads the diff, updates or generates the tests, runs them, and comments on the PR with the outcome — including a recorded browser session for UI tests.

This repo is a self-contained, runnable demo of that workflow.

---

## What problem this solves

Engineering teams ship code faster than QA can validate it. The bottleneck is:

1. Engineers open a PR that changes an API or a UI flow.
2. QA has to read the diff, figure out what tests are affected, write or update them, run them, and report back.
3. By the time QA catches up, more PRs have landed.

This demo automates step 2. When a PR lands, an agent:

- **For APIs**: reads the diff, identifies affected endpoints, updates the test suite (or generates a new one for a greenfield endpoint), runs it against the real API, and posts the results to the PR.
- **For UIs**: reads a natural-language workflow description, drives a real browser through the flow, generates a maintainable Playwright spec, records the session, and posts the video + results to the PR.

The team keeps the tests the agent emits. They are not throwaway — they follow the same conventions a careful human would write.

---

## The three scenarios in this repo

| # | Scenario | What the agent does | What the PR shows |
|---|---|---|---|
| 1 | **Existing API + PR adds a parameter** | Reads the diff, identifies which tests cover the changed endpoint, updates them to exercise the new parameter, runs the suite against the real API | Bot comment with updated test count + pass/fail table |
| 2 | **Brand-new API endpoint with no tests** | Reads the endpoint definition, generates a test plan, writes pytest cases, runs them | Bot comment with the generated test plan + results |
| 3 | **UI workflow described in natural language** | Drives a real browser via Playwright, generates a maintainable spec following accessibility-first conventions, runs it, records the session | Bot comment with status table, **recorded video**, and the generated spec file linked |

All three are triggered the same way: a PR lands → the OpenHands Automation service dispatches the right agent → the agent posts back to the PR.

---

## How it's built (the OpenHands angle)

This repo is intentionally *composed*, not custom-built. Every capability below is an off-the-shelf OpenHands feature:

| Capability | What it gives the demo |
|---|---|
| **OpenHands Automation service** | The PR-trigger layer. Webhook-triggered when your environment has public ingress; cron-poll-triggered when it doesn't. Both configs are shipped. See [`automations/`](./automations/). |
| **OpenHands SDK + skills** | The agents themselves. The QA conventions and Playwright patterns are encoded as **skills** (markdown files), not Python code. Your team customizes the agent's behavior by editing markdown. See [`skills/`](./skills/). |
| **BrowserToolSet (Playwright, shipped today)** | UI automation. Not a roadmap item — the agent drives a real Chromium browser using a tool that's already in the SDK. |
| **rrweb browser session recording** | Every UI run produces a replayable recording attached to the PR comment. Built-in audit trail. |
| **LLM profile store** | Model-agnostic. Swap between Claude, OpenAI, or any OpenAI-compatible local endpoint (vLLM, LiteLLM proxy, etc.) by changing one config file. See [`llm-profiles/`](./llm-profiles/). |
| **Secrets store** | API keys (YouTube Data API), tokens (GitHub), test credentials — live in the OpenHands secrets store, never in code or env files. |
| **Docker sandbox** | The agent server runs in an isolated container on your infrastructure. The demo can run entirely offline once configured. |

The customer-facing summary: **self-hosted, model-agnostic, customizable** — all three pillars are covered by composition. There is almost no agent code in this repo. There is configuration, skills, scenarios, and a thin PR reporter.

---

## Repo layout

```
automated-qa-demo/
├── README.md                          # You are here
├── automations/                       # OpenHands Automation service configs
│   ├── api-qa-event-trigger.json      # Webhook-triggered (public ingress)
│   ├── api-qa-cron-poll.json          # Cron-poll fallback (no public ingress)
│   └── ui-qa-event-trigger.json
├── llm-profiles/                      # Model-agnostic profiles
│   ├── claude-sonnet.json
│   ├── gpt5.json
│   └── self-hosted-litellm.json
├── skills/                            # Behavior customization (no code)
│   ├── webapp-testing/                # Vendored from anthropics/skills
│   ├── front-end-testing/             # Vendored from citypaul/.dotfiles
│   └── api-qa-conventions/            # Authored for this demo (pytest + httpx)
├── scenarios/
│   ├── 01_api_pr_update/              # YouTube Data API wrapper service + the PR diff
│   ├── 02_api_new_generation/         # A new endpoint with no tests
│   └── 03_ui_workflow/                # saucedemo.com + workflow.md
├── agents/
│   ├── api_qa_agent.py                # Loads api-qa-conventions skill
│   └── ui_qa_agent.py                 # Loads webapp-testing + front-end-testing skills
├── reporters/
│   └── pr_comment.py                  # Markdown bot comment (agent-canvas style)
├── .github/workflows/
│   ├── qa-api-on-pr.yml               # GH Actions handoff to Automation service
│   └── qa-ui-on-pr.yml
└── docs/
    ├── architecture.md                # Diagram + data flow
    ├── self-hosted-llm.md             # How to point at a local OpenAI-compatible endpoint
    ├── security-and-audit.md          # rrweb, secrets, sandbox, persistence
    ├── bitbucket-port.md              # 1-page mapping to Bitbucket Pipelines (future)
    └── demo_script.md                 # Talking points + sample timing
```

---

## Quick start (for reviewers running the demo themselves)

> **Status:** see [`docs/runbook.md`](./docs/runbook.md) once Phase 1 lands. Until then this section is a placeholder.

```bash
# 1. Clone and install
git clone <this repo>
cd automated-qa-demo
uv sync

# 2. Configure secrets (YouTube API key, GitHub token)
cp .env.example .env
$EDITOR .env

# 3. Register the automation with your OpenHands instance
./scripts/register-automations.sh

# 4. Open a PR against the demo repo
gh pr create --title "Add regionCode to /search" --body "..." --head demo/add-region-code

# 5. Watch the agent comment back on the PR
```

---

## Roadmap of this scaffold

| Phase | Deliverable | Status |
|---|---|---|
| 1 | Top-level README + folder skeleton | ✅ this commit |
| 2 | Skills (vendor 2, author 1) | ⏳ next |
| 3 | Scenario 1 — existing API + PR | ⏳ |
| 4 | Scenario 2 — new API | ⏳ |
| 5 | Scenario 3 — UI workflow + session recording | ⏳ |
| 6 | Agents (`api_qa_agent.py`, `ui_qa_agent.py`) | ⏳ |
| 7 | Automation service configs (event + cron-poll) | ⏳ |
| 8 | LLM profile store | ⏳ |
| 9 | PR comment reporter | ⏳ |
| 10 | Docs (architecture, self-hosted LLM, security, demo script) | ⏳ |
