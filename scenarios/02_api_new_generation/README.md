# Scenario 2 — Brand-new endpoint with no tests

**The QA goal:** when a PR adds a new endpoint with no test coverage, the
agent reads the endpoint definition, writes a test plan, generates the test
file, and runs it.

## What's in this folder

```
02_api_new_generation/
├── pr/
│   ├── add-playlists-endpoint.patch   # The new endpoint (no tests included)
│   └── PR_DESCRIPTION.md
└── README.md
```

This scenario **shares the service** from [Scenario 1](../01_api_pr_update/).
The PR here is applied to the same `service/app.py`. We don't duplicate the
service — that would imply "different system" when really it's the same
codebase evolving over multiple PRs.

## What the agent does

1. Read the PR diff and description (`pr/`).
2. Apply the patch to the service (`patch -p1`).
3. Recognize this is a **brand-new endpoint** (no `tests/test_playlists.py` exists).
4. Follow the **"When you generate tests for a brand-new endpoint"**
   section of the [`api-qa-conventions` skill](../../skills/api-qa-conventions/SKILL.md):
   - Write the test plan as a comment block at the top of the new file.
   - Implement each scenario per the error-path coverage table.
5. Run the full suite — including the new tests — against the real YouTube API.
6. Post results to the PR.

## Why this scenario matters for the demo

This is the customer's "**brand-new API**" use case: agent creates docs +
test plan + automation cases from a fresh endpoint. The difference from
Scenario 1 is that the agent has to *think about coverage* from scratch
rather than extend existing tests. Same skill, different invocation path.

## How to run

```bash
# Apply the PR
cd scenarios/01_api_pr_update
patch -p1 < ../02_api_new_generation/pr/add-playlists-endpoint.patch

# Then run the agent (wired up once Phase 6 lands)
gh pr edit <number> --add-label "openhands-qa"
```

The automation detects scenario 02 from the branch name or changed files,
generates `test_playlists.py` from scratch, commits it to the branch, and
posts a results comment.
