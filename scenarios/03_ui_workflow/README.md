# Scenario 3 — UI workflow on a real site

**The QA goal:** given a natural-language workflow description, the agent
drives a real browser, generates a maintainable Playwright spec, runs it,
records the session, and posts the video + results to the PR.

## What's in this folder

```
03_ui_workflow/
├── workflow.md             # The natural-language workflow to test
├── generated_specs/        # The agent writes spec files here
│   └── .gitkeep
├── recordings/             # rrweb session recordings land here
│   └── .gitkeep
└── README.md
```

There is no application code in this scenario — the system under test is
the public [saucedemo.com](https://www.saucedemo.com/v1/) site.

## What the agent does

1. Read `workflow.md`.
2. Load the [`webapp-testing`](../../skills/webapp-testing/) skill (runtime
   pattern — Playwright reconnaissance-then-action).
3. Load the [`front-end-testing`](../../skills/front-end-testing/) skill
   (quality bar — accessibility-first queries, idempotency, etc.).
4. Drive a real Chromium browser through the workflow:
   - Navigate, wait for `networkidle`, screenshot, identify selectors.
   - Execute each step in order.
   - Record the entire session with rrweb.
5. Generate a standalone Playwright spec at
   `generated_specs/checkout-backpack.spec.ts` that any QA engineer can
   re-run with `npx playwright test`.
6. Run the generated spec to confirm it passes outside the agent.
7. Post a PR comment with status, the generated spec file linked, and the
   rrweb recording embedded as a video.

## Why this scenario matters for the demo

This is the customer's UI-automation question made concrete: *"Can the
agent actually do UI automation today?"*

The answer this scenario gives is **yes, with zero new agent code**:

- The Playwright runtime is provided by the SDK's `BrowserToolSet`.
- The "how to use Playwright" knowledge comes from the vendored
  `webapp-testing` skill.
- The "what good tests look like" knowledge comes from the vendored
  `front-end-testing` skill.
- The browser session recording is a stock OpenHands feature.

The customer sees a generated spec, a passing run, and a watchable video —
not a slide deck.

## How to run

```bash
# Wired up once Phase 6 lands.
python -m agents.ui_qa_agent \
    --scenario scenarios/03_ui_workflow \
    --workflow scenarios/03_ui_workflow/workflow.md
```

## Out of scope (deliberately)

- We are **not** building our own demo site. saucedemo is real, stable,
  and intentionally built for testing. Replacing it with our own toy app
  would weaken the demo, not strengthen it.
- We are not doing visual regression. That's a different problem; this
  scenario is about workflow-level functional testing.
