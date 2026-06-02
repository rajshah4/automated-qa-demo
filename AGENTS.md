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

1. **Feature change only — no tests.** The whole point of the demo is that the
   automation adds the tests. A demo PR must contain only the production code
   change (`service/app.py`). Never commit test file changes in this step.

2. **Apply the canned patch for the scenario:**
   - Scenario 01: `patch -p1 < scenarios/01_api_pr_update/pr/add-region-and-max-results.patch`
     (run from repo root)
   - Scenario 02: `patch -p1 < scenarios/02_api_new_generation/pr/add-playlists-endpoint.patch`
     (run from repo root, applies on top of scenario 01's service)

3. **Branch naming:** `demo/<short-slug>`, e.g. `demo/search-region-maxresults`.

4. **PR description** must describe only the feature change — what the new
   parameters do, their types/constraints, and what HTTP status invalid values
   return. Do not mention tests or the QA agent. Copy the style from the
   scenario's own `pr/PR_DESCRIPTION.md`.

5. **Apply the `openhands-qa` label** after the PR is open. This is the trigger
   for the automation. Create the label first if it doesn't exist:
   `gh label create "openhands-qa" --color "0075ca" --description "Trigger OpenHands automated QA"`

6. **Do not run tests** during this setup step. Tests are the automation's job.

**Fastest correct invocation:**
> "Create the demo PR for scenario 01. Feature change only, openhands-qa label, no tests."

## Where to learn more

- The top-level [`README.md`](./README.md) is the customer-facing pitch.
- Each scenario has its own `README.md` with run instructions.
- [`automations/README.md`](./automations/README.md) documents the registered
  OpenHands Automation that invokes you.
