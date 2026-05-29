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
- **There is no "agent code"** in this repo other than thin conversation-starter
  scripts in `agents/`. The behavior of QA work is encoded in the skills.

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

## Where to learn more

- The top-level [`README.md`](./README.md) is the customer-facing pitch.
- Each scenario has its own `README.md` with run instructions.
- The `agents/` folder contains the conversation-starter scripts that run
  *outside* the sandbox to invoke you.
