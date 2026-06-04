# automated-qa-demo — project guide for OpenHands agents

This repository is a runnable demo: when a PR lands, an agent reads the diff,
updates or generates tests, runs them, and posts results back to the PR.

If you (the agent) are reading this, you are running inside an OpenHands Cloud
sandbox that has cloned this repo into your workspace. Read this file first
before doing any work.

## What you should know about this repo

- **Three scenarios** live under `scenarios/`. Each is self-contained:
  - `01_api_pr_update/` — an existing API gets new params; update tests.
  - `02_api_new_generation/` — a brand-new endpoint with no tests; generate them.
  - `03_ui_workflow/` — drive a real site via Playwright and emit a spec.
- **Three skills** live under `skills/`. **You must follow these when working
  in this repo.** Load and read them at the start of your task:
  - `skills/api-qa-conventions/SKILL.md` — pytest + httpx conventions for API tests.
  - `skills/webapp-testing/SKILL.md` — runtime Playwright pattern for UI work.
  - `skills/front-end-testing/SKILL.md` — quality bar for emitted UI specs.
- **There is no "agent code"** in this repo. The behavior of QA work is encoded
  entirely in the skills. You are invoked by the OpenHands Automation whose
  prompt lives in `automations/build_prompt.py`.

## How to behave when invoked

1. **Read your task description carefully.** It will tell you which scenario
   to work on and what you're being asked to do.
2. **Read the relevant skill file(s) before you start writing code.** The
   skill is the source of truth for conventions in this repo.
3. **Work in the scenario folder.** Do not modify files outside the scenario
   you've been assigned to unless the task explicitly tells you to.
4. **Run tests against real APIs / real browsers.** Do not mock the system
   under test. Skills explain when mocking the *upstream* is acceptable.
5. **Report back via the task's stated output channel.** Typically:
   - For API scenarios: print the pytest summary and write a markdown report
     to `/tmp/qa-report.md`.
   - For UI scenarios: ensure the generated spec lives in
     `scenarios/03_ui_workflow/generated_specs/`, the recording lives in
     `scenarios/03_ui_workflow/recordings/`, and write a report to
     `/tmp/qa-report.md`.

## Conventions

- Python: 3.11+, formatted naturally (no special formatter required for the demo).
- TypeScript: only inside `scenarios/03_ui_workflow/generated_specs/`.
- Do not introduce new top-level dependencies without an explicit task instruction.
- Never commit secrets. The YouTube API key and any GitHub token come from
  the sandbox's environment.

## Creating a demo PR (human-triggered setup task)

When asked to "create a demo PR" or "set up a PR for scenario N":

### Background: why a base branch is needed

`main` already contains the feature code from previous demo runs. To produce a
meaningful PR diff (which the QA automation reads), each scenario has a
permanent base branch that is pinned to the pre-feature commit:

| Scenario | Base branch | Pinned commit |
|---|---|---|
| 01 | `demo-base/01` | `c943c99` |
| 02 | `demo-base/02` | _(same as 01 base, after 01 patch)_ |

Open every demo PR against its base branch, **not** `main`.

### Steps

1. **Feature change only — no tests.** The whole point of the demo is that the
   automation adds the tests. A demo PR must contain only the production code
   change (`service/app.py`). Never commit test file changes in this step.

2. **Set up the base branch** (skip if it already exists on the remote):
   ```bash
   git checkout c943c99 -b demo-base/01
   git push -u origin demo-base/01
   git checkout main
   ```

3. **Create the feature branch from the base and apply the patch:**
   ```bash
   # Scenario 01
   git checkout demo-base/01 -b demo/search-region-maxresults
   cd scenarios/01_api_pr_update && patch -p1 < pr/add-region-and-max-results.patch && cd ../..
   git add scenarios/01_api_pr_update/service/app.py
   git commit -m "feat(search): add regionCode and maxResults to GET /search"
   git push -u origin demo/search-region-maxresults --force
   ```
   *(Force-push is expected — demo branches are reused across runs.)*

4. **Open the PR** targeting `demo-base/01` (not `main`). Copy the PR
   description from `scenarios/01_api_pr_update/pr/PR_DESCRIPTION.md`.

5. **Apply the `openhands-qa` label** immediately after opening the PR — this
   is the trigger for the automation:
   ```bash
   gh pr edit <PR_NUMBER> --repo <owner>/automated-qa-demo --add-label "openhands-qa"
   ```
   Create the label first if it doesn't exist:
   ```bash
   gh label create "openhands-qa" --color "0E8A16" --description "Trigger OpenHands Automation QA run"
   ```

6. **Do not run tests** during this setup step. Tests are the automation's job.

**Fastest correct invocation:**
> "Create the demo PR for scenario 01. Feature change only, openhands-qa label, no tests."

## Where to learn more

- The top-level [`README.md`](./README.md) is the customer-facing pitch.
- Each scenario has its own `README.md` with run instructions.
- [`automations/README.md`](./automations/README.md) documents the registered
  OpenHands Automation that invokes you.
