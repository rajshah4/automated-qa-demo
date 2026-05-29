---
name: api-qa-conventions
description: Conventions for authoring and updating API integration tests in this repo. Use when reading a PR diff that changes an API surface, when generating tests for a brand-new endpoint, or when running an existing pytest suite against a real HTTP API. Covers test layout, naming, the pytest+httpx pattern used here, fixtures, assertions, error-path coverage, and how to keep tests honest (real network calls — no implementation-mocking of the system under test).
---

# API QA Conventions

This skill teaches the agent **how this team writes API tests** so the tests it
generates and updates feel native — same structure, same naming, same level
of error-path coverage as if a careful human had written them.

If you are about to add, modify, or generate a test for an HTTP endpoint
in this repo, read this first. Everything below is non-negotiable unless the
PR explicitly proposes a change to the conventions themselves.

## Stack

- **Test runner:** `pytest`
- **HTTP client under test:** `httpx` (sync `httpx.Client` — async only if the
  service under test requires it)
- **Test data:** plain dataclasses or dicts. No factory libraries.
- **Fixtures:** `pytest` fixtures, scope explicitly declared on every fixture.
- **Live API calls go through the wrapper service**, never directly to the
  third-party API. The wrapper is the system under test.

## Test layout

```
service/
├── app.py
└── tests/
    ├── conftest.py                 # client fixture, auth fixture, common factories
    ├── test_<endpoint>.py          # one test file per endpoint group
    └── test_<endpoint>_errors.py   # error-path tests live in a sibling file
                                    #   (only when there's enough of them to
                                    #   warrant the split — otherwise inline)
```

Rules:

- **One test file per endpoint group**, not per HTTP method. `/search`,
  `/videos`, `/channels` each get their own file.
- **Error-path tests can live inline** in the same file until the file grows
  past ~300 lines; then split into a `_errors.py` sibling.
- **Never** put unrelated endpoints in the same file just because they share
  a fixture.

## Naming

Test function names follow this shape:

```
test_<endpoint>_<scenario>_<expected_outcome>
```

Examples:

- `test_search_default_params_returns_results`
- `test_search_with_region_code_filters_results`
- `test_search_missing_query_param_returns_400`
- `test_videos_unknown_id_returns_404`

Do **not** name tests after the HTTP verb (`test_get_search_...`). The verb
is incidental; the scenario is what matters.

## The pytest + httpx pattern

```python
def test_search_default_params_returns_results(client):
    response = client.get("/search", params={"q": "openhands"})

    assert response.status_code == 200
    body = response.json()
    assert "items" in body
    assert len(body["items"]) > 0
    assert all("videoId" in item for item in body["items"])
```

Every test follows the same three-block shape:

1. **Act** — issue the request.
2. **Assert status** — always check `status_code` first, before anything else.
3. **Assert shape and content** — check the response body has the expected
   structure *and* meaningful values. Don't only check that a key exists;
   check that it's populated correctly.

## Real network calls vs. mocking

**The service under test is exercised over real HTTP.** The wrapper service
under test is started in-process (via the `client` fixture); the *third-party*
API it calls (e.g., YouTube Data API) is hit for real using a test API key.

**Do not mock the third-party API** unless the test is specifically about
error handling and the error is hard to provoke (e.g., 5xx). When you do
need to mock, use `respx` (httpx-native) — never `unittest.mock` on `httpx`
internals.

**Rationale:** if the third-party changes its contract, our tests should
catch it before our wrapper ships broken behavior to consumers. That's the
whole point of integration tests.

## Fixtures

```python
# conftest.py
import os
import pytest
from fastapi.testclient import TestClient
from service.app import app


@pytest.fixture(scope="session")
def youtube_api_key() -> str:
    key = os.environ.get("YOUTUBE_API_KEY")
    if not key:
        pytest.skip("YOUTUBE_API_KEY not set; skipping live API tests")
    return key


@pytest.fixture(scope="session")
def client(youtube_api_key: str) -> TestClient:
    # Wrapper service reads YOUTUBE_API_KEY from env; ensure it's set.
    return TestClient(app)
```

Rules:

- **Always declare `scope=` explicitly** on every fixture. No implicit
  `function` scope.
- **Skip — don't fail — when external credentials are missing.** A missing
  API key is an environment problem, not a code problem.
- **Never share mutable state across tests.** Session-scoped fixtures must be
  read-only.

## Error-path coverage

For every endpoint, the suite must cover at minimum:

| Scenario | Expected status |
|---|---|
| Happy path with all params present | 200 |
| Required param missing | 400 |
| Invalid param value (wrong type, out of range) | 400 |
| Resource not found (where applicable) | 404 |
| Auth missing / invalid (where applicable) | 401 / 403 |
| Upstream API failure (mocked with `respx`) | 502 or 503, depending on the wrapper's contract |

If a new endpoint is added without these, the PR is incomplete.

## When you update tests in response to a PR diff

When a PR adds a new query parameter to an existing endpoint:

1. **Identify the affected test file** by mapping the changed endpoint to
   `tests/test_<endpoint>.py`.
2. **Add at least two new tests**:
   - One that exercises the happy path with the new parameter set.
   - One that exercises the new parameter's validation (invalid value → 400).
3. **Do not delete or rename existing tests** unless the PR's diff explicitly
   removes the corresponding behavior. The existing tests are the regression
   safety net.
4. **Update fixtures only if the new parameter is required** for the existing
   happy-path tests to still pass. Otherwise leave fixtures alone.

## When you generate tests for a brand-new endpoint

1. Read the endpoint's definition in `service/app.py`.
2. **Write the test plan first** as a comment block at the top of the new
   test file — list every scenario you intend to cover. Use the
   error-path-coverage table above as the minimum bar.
3. Implement each scenario as a test following the three-block pattern.
4. Run the suite locally. Every test you wrote must pass before opening the
   PR.

## What never to do

- **Never** assert against the third-party API's response shape directly.
  Always assert against the wrapper's response shape. The wrapper is the
  contract.
- **Never** use `time.sleep()` to wait for upstream state. If a test needs
  to wait, it's testing the wrong thing.
- **Never** introduce `pytest-asyncio` unless the service is genuinely async.
  Sync tests are faster to read and debug.
- **Never** put credentials in test code. Use fixtures that read from env,
  and skip when missing.
- **Never** commit a flaky test. If a test depends on a third-party that
  occasionally rate-limits, gate it behind a marker (`@pytest.mark.live`)
  and exclude it from the default run.
