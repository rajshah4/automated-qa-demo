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

## How it's built

This repo is intentionally *composed*, not custom-built. Almost everything below is an off-the-shelf OpenHands feature; the demo-specific code is small and focused.

| Capability | Where it lives | What it does |
|---|---|---|
| **V1 Conversation API** | [`agents/`](./agents/) | Conversation-starter scripts that POST a self-contained task prompt to OpenHands Cloud. The real work runs inside the conversation's own sandbox. No agent code ships to the sandbox — only a prompt. |
| **Skills (markdown)** | [`skills/`](./skills/) | Behavior customization without code. Three skills auto-load via `AGENTS.md`: vendored `webapp-testing` (Anthropic), vendored `front-end-testing` (citypaul), and authored `api-qa-conventions` (this repo). Your team customizes the agent by editing markdown. |
| **BrowserToolSet (Playwright)** | UI scenario | The sandbox already ships with a real Chromium and the OpenHands BrowserToolSet. The UI agent uses it via Playwright with `trace: 'on'`, `video: 'on'`, `screenshot: 'only-on-failure'`. |
| **Sandbox secrets** | OpenHands platform | `YOUTUBE_API_KEY`, `GITHUB_TOKEN`, etc. live in the OpenHands secrets store and are injected into the sandbox at runtime. Never in code or `.env` files. |
| **Docker sandbox** | OpenHands platform | The conversation runs in an isolated container with its own filesystem. The demo can run end-to-end without exposing the customer's network. |
| **OpenHands Automation** | (production target) | The PR-trigger layer. Watches the repo via GitHub webhook in connected environments, or via cron-poll in air-gapped ones. When a PR matches a configured pattern, the automation dispatches the right conversation, fetches artifacts, and posts the result back to the PR. **No CI YAML for the customer to maintain.** |

The customer-facing summary: **self-hosted, model-agnostic, customizable** — all three are covered by composition. The whole repo is two thin conversation-starter scripts, three skills, and the scenario fixtures. There is no bespoke agent runtime to maintain.

> **Both trigger paths are live on this repo.** When a PR opens, two independent
> pipelines fire in parallel:
>
> 1. **OpenHands Automation** (registered on OpenHands Cloud, automation ID
>    `5d152cb1-bb58-4402-9839-063fd9e76fe5`, model: GPT-5.5) — the
>    production-target architecture. Apply the `openhands-qa` label to any PR
>    and the automation fires within ~2 seconds, detects the scenario from the
>    changed files, runs the QA conversation, and posts a
>    🤖 **Automated QA (via OpenHands Automation)** comment to the PR.
>
> 2. **GitHub Actions** ([`qa.yml`](./.github/workflows/qa.yml)) — kept as a
>    fallback and reference. Posts the ✅ **Automated QA —** comment.
>
> Both comments appear on the same PR. Seeing them side-by-side is the demo:
> the customer can compare the two trigger paths and confirm they produce
> functionally equivalent results. See [`automations/README.md`](./automations/README.md)
> for full details on the registered automation.

---

## Repo layout

```
automated-qa-demo/
├── README.md                          # You are here
├── AGENTS.md                          # Auto-loaded by the OpenHands sandbox
├── runs.jsonl                         # Local ledger of conversations + cost/timing
├── .github/workflows/
│   └── qa.yml                         # Single workflow: dispatch → fetch → GIF → comment
├── agents/
│   ├── api_qa_agent.py                # Starts the conversation for scenarios 1 & 2
│   ├── ui_qa_agent.py                 # Starts the conversation for scenario 3
│   ├── fetch_artifacts.py             # Pulls the sandbox's working tree post-run
│   ├── runs.py                        # CLI for the runs.jsonl ledger
│   ├── _client.py                     # Tiny V1 API client (httpx)
│   ├── _ci.py                         # GITHUB_OUTPUT helpers
│   └── README.md                      # How the conversation-starter pattern works
├── automations/
│   └── README.md                      # Registered OpenHands Automation details + runbook
├── skills/
│   ├── api-qa-conventions/            # Authored — pytest + httpx + brownfield rules
│   ├── webapp-testing/                # Vendored from anthropics/skills
│   └── front-end-testing/             # Vendored from citypaul/.dotfiles
├── scenarios/
│   ├── 01_api_pr_update/              # YouTube wrapper service + PR diff (regionCode)
│   ├── 02_api_new_generation/         # New /playlists endpoint with no tests
│   └── 03_ui_workflow/                # saucedemo.com + natural-language workflow.md
└── docs/
    └── from-the-customer.md           # Open design questions surfaced in demo calls
```

---

## Quick start

The demo is already wired up against `rajshah4/automated-qa-demo`. Three open PRs show the three scenarios live:

| PR | Scenario | What happens when it opens |
|---|---|---|
| [#2](https://github.com/rajshah4/automated-qa-demo/pull/2) | API param change | Agent reads the diff, extends `test_search.py` with five new tests, runs the suite, posts results |
| [#3](https://github.com/rajshah4/automated-qa-demo/pull/3) | Fresh API endpoint | Agent recognizes no `test_playlists.py` exists, generates one from scratch following the skill, runs the suite, posts results |
| [#4](https://github.com/rajshah4/automated-qa-demo/pull/4) | UI workflow | Agent writes a Playwright spec, drives a real browser through saucedemo, captures video + traces + HTML report. PR comment embeds a 250 KB GIF replay inline |

### Trigger a run yourself

Three ways:

```bash
# 1. Open a PR that touches a scenario folder — workflow fires automatically.
gh pr create --title "..." --body "..." --head my-branch --base main

# 2. Manually dispatch a specific scenario from the Actions tab.
gh workflow run qa.yml -f scenario=scenarios/03_ui_workflow

# 3. Run the conversation-starter locally against the OpenHands API.
export OPENHANDS_API_KEY=...
python -m agents.api_qa_agent --scenario scenarios/01_api_pr_update --wait
```

The PR-triggered path is the customer-visible flow; the other two are for development.

### What you'll see on a PR

- Status table (duration, cost, conversation URL, artifact bundle link)
- For UI scenarios: an inline auto-playing GIF of the test run + the full Playwright HTML report, traces, and HD `.webm` videos in the downloadable artifact bundle
- For API scenarios: the modified/created test files in the artifact bundle, with a `qa-report.md` explaining what the agent did and why
