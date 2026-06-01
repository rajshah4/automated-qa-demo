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
| 1 | **Existing API + PR adds a parameter** | Reads the diff, identifies which tests cover the changed endpoint, updates them to exercise the new parameter, runs the suite against the real API | Test file committed to branch + 🤖 comment with full report and collapsible test code |
| 2 | **Brand-new API endpoint with no tests** | Reads the endpoint definition, generates a test plan, writes pytest cases, runs them | New test file committed to branch + 🤖 comment with generated test plan and collapsible code |
| 3 | **UI workflow described in natural language** | Drives a real browser via Playwright, generates a maintainable spec, runs it, records the session | Specs + GIF previews committed to branch + 🤖 comment with **inline GIF replays**, full report, and collapsible spec code |

All three are triggered the same way: apply the `openhands-qa` label to a PR → the OpenHands Automation fires within ~2 seconds → the agent generates tests, commits them to the branch, and posts results back to the PR.

---

## How it's built

This repo is intentionally *composed*, not custom-built. Almost everything below is an off-the-shelf OpenHands feature; the demo-specific code is small and focused.

| Capability | Where it lives | What it does |
|---|---|---|
| **OpenHands Automation** | [`automations/`](./automations/) | The PR-trigger layer. Registered on OpenHands Cloud — when the `openhands-qa` label is applied to a PR, the automation fires, detects the scenario, runs the full QA conversation, commits artifacts, and posts results. **No CI YAML to maintain.** |
| **Skills (markdown)** | [`skills/`](./skills/) | Behavior customization without code. Three skills auto-load via `AGENTS.md`: vendored `webapp-testing` (Anthropic), vendored `front-end-testing` (citypaul), and authored `api-qa-conventions` (this repo). Your team customizes the agent by editing markdown. |
| **BrowserToolSet (Playwright)** | UI scenario | The sandbox ships with a real Chromium and the OpenHands BrowserToolSet. The UI agent uses Playwright with `trace: 'on'`, `video: 'on'`, converts recordings to GIF previews. |
| **Sandbox secrets** | OpenHands platform | `YOUTUBE_API_KEY`, `GITHUB_TOKEN`, etc. live in the OpenHands secrets store and are injected at runtime. Never in code or `.env` files. |
| **Docker sandbox** | OpenHands platform | The conversation runs in an isolated container with its own filesystem. End-to-end without exposing the customer's network. |

The customer-facing summary: **self-hosted, model-agnostic, customizable** — all three are covered by composition. The whole repo is one automation prompt, three skills, and the scenario fixtures. There is no bespoke agent runtime to maintain.

> **OpenHands Automation is live on this repo.** Apply the `openhands-qa` label to any PR
> and within ~2 seconds a registered OpenHands Cloud Automation fires:
> it detects the scenario from the PR's changed files, runs the full QA conversation,
> commits the generated test files and GIF previews directly to the PR branch, and posts a
> 🤖 **Automated QA (via OpenHands Automation)** comment with inline results, the full QA
> report, and collapsible generated-file contents — everything visible without leaving the PR.
>
> Automation ID: `5d152cb1-bb58-4402-9839-063fd9e76fe5` — see [`automations/README.md`](./automations/README.md).

---

## Repo layout

```
automated-qa-demo/
├── README.md                          # You are here
├── AGENTS.md                          # Auto-loaded by the OpenHands sandbox
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

The demo is already wired up against `rajshah4/automated-qa-demo`. Three open PRs show the three scenarios live — each has the `openhands-qa` label applied and a completed 🤖 comment:

| PR | Scenario | What the automation did |
|---|---|---|
| [#14](https://github.com/rajshah4/automated-qa-demo/pull/14) | API param change (`regionCode` + `maxResults`) | Updated `test_search.py`, committed it to branch, posted 🤖 comment with full report + collapsible test code |
| [#15](https://github.com/rajshah4/automated-qa-demo/pull/15) | Fresh API endpoint (`/playlists`) | Generated `test_playlists.py` from scratch, committed to branch, posted 🤖 comment with test plan + collapsible code |
| [#16](https://github.com/rajshah4/automated-qa-demo/pull/16) | UI workflow (cart badge edge case) | Wrote Playwright specs, recorded session, committed specs + GIF previews to branch, posted 🤖 comment with **inline GIF replays** + collapsible spec files |

### Trigger a run yourself

```bash
# 1. Open a PR that touches a scenario folder, then apply the label — automation fires.
gh pr create --title "..." --body "..." --head my-branch --base main
gh pr edit <number> --add-label "openhands-qa"

# 2. Manually dispatch (no event payload — agent falls back to most-recently-labeled PR).
source .env
curl -s -X POST \
  "https://app.all-hands.dev/api/automation/v1/5d152cb1-bb58-4402-9839-063fd9e76fe5/dispatch" \
  -H "Authorization: Bearer $OPENHANDS_API_KEY"

```

The label-triggered Automation path is the customer-visible flow; options 2 and 3 are for development.

### What you'll see on a PR

- Status table (duration, cost, conversation URL, artifact bundle link)
- For UI scenarios: an inline auto-playing GIF of the test run + the full Playwright HTML report, traces, and HD `.webm` videos in the downloadable artifact bundle
- For API scenarios: the modified/created test files in the artifact bundle, with a `qa-report.md` explaining what the agent did and why
