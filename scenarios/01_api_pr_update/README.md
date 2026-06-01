# Scenario 1 — Existing API + PR that adds parameters

**The QA goal:** when a PR adds new parameters to an existing endpoint, the
agent updates the test suite to cover them, runs it, and posts results to
the PR.

## What's in this folder

```
01_api_pr_update/
├── service/
│   ├── app.py                  # FastAPI wrapper around YouTube Data API v3
│   └── tests/                  # Existing pytest suite (the "before" state)
│       ├── conftest.py
│       ├── test_search.py
│       ├── test_videos.py
│       └── test_channels.py
├── pr/
│   ├── add-region-and-max-results.patch   # The "change" the agent reacts to
│   └── PR_DESCRIPTION.md                  # The PR title/description
├── pyproject.toml
└── README.md
```

## Quick start

```bash
cd scenarios/01_api_pr_update
uv venv && uv pip install -e ".[test]"
export YOUTUBE_API_KEY=<your-key>

# Baseline: existing tests should pass against the unchanged service
pytest

# Simulate the PR landing
patch -p1 < pr/add-region-and-max-results.patch

# Without test updates, the new behavior is uncovered. The agent's job is
# to update tests so they exercise the new params.
pytest
```

## What the agent does

The OpenHands Automation detects this scenario from the changed files, reads
`AGENTS.md` and the `api-qa-conventions` skill, then:

1. Identifies `service/tests/test_search.py` as the affected file.
2. Adds tests for the happy path with both new params.
3. Adds validation tests for `regionCode` (length checks) and `maxResults`
   (range checks).
4. Leaves other test files untouched.
5. Commits the updated test file to the PR branch and posts a results comment.

## How to trigger

Open a PR from a branch that touches this scenario, then apply the
`openhands-qa` label - the automation fires within ~2 seconds:

```bash
gh pr edit <number> --add-label "openhands-qa"
```

## Why this scenario matters for the demo

This is the customer's #1 stated use case ("Existing API changes: Agent
detects new parameters in PR, updates test suite automatically"). It shows
the full PR-in / tests-out loop end-to-end against a real third-party API,
using nothing but composition (SDK + the `api-qa-conventions` skill).
