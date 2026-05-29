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

The `api_qa_agent` (see [`agents/api_qa_agent.py`](../../agents/api_qa_agent.py))
is invoked with:

- The PR diff (`pr/add-region-and-max-results.patch`)
- The PR description (`pr/PR_DESCRIPTION.md`)
- Read/write access to `service/` and `service/tests/`
- The `api-qa-conventions` skill loaded (defines how tests should be written)

Following the skill's "When you update tests in response to a PR diff"
section, the agent will:

1. Identify `service/tests/test_search.py` as the affected file.
2. Add tests for the happy path with both new params.
3. Add validation tests for `regionCode` (length checks) and `maxResults`
   (range checks).
4. Leave the other test files untouched (the diff doesn't affect them).
5. Run the suite and post the result to the PR.

## How to run the agent against this scenario

> Wired up once `agents/api_qa_agent.py` lands in Phase 6.

```bash
python -m agents.api_qa_agent \
    --scenario scenarios/01_api_pr_update \
    --pr-diff scenarios/01_api_pr_update/pr/add-region-and-max-results.patch \
    --pr-description scenarios/01_api_pr_update/pr/PR_DESCRIPTION.md
```

## Why this scenario matters for the demo

This is the customer's #1 stated use case ("Existing API changes: Agent
detects new parameters in PR, updates test suite automatically"). It shows
the full PR-in / tests-out loop end-to-end against a real third-party API,
using nothing but composition (SDK + the `api-qa-conventions` skill).
