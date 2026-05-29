# PR: Add `regionCode` and `maxResults` to /search

## Summary

Adds two optional query parameters to `GET /search`:

- **`regionCode`** — 2-letter ISO 3166-1 alpha-2 country code (e.g. `US`, `GB`,
  `IN`). When set, restricts results to videos available in that region.
- **`maxResults`** — integer 1–50, default 25. Controls the number of items
  returned in the response.

Both are passed through to the YouTube Data API. The wrapper's response
shape is unchanged.

## Why

Two consumer teams have asked for region-scoped search. `maxResults` falls
out for free since the YT API already supports it and we were always sending
the default (5 from upstream's side, now explicitly 25).

## Test plan

The QA agent will:

1. Read the diff (this patch).
2. Update `service/tests/test_search.py` to cover:
   - happy path: `/search?q=...&regionCode=US&maxResults=10` → 200, ≤10 items
   - validation: `regionCode=USA` (3 letters) → 422
   - validation: `regionCode=U` (1 letter) → 422
   - validation: `maxResults=0` → 422
   - validation: `maxResults=51` → 422
3. Run the full suite against the real YouTube API.
4. Post results as a PR comment.

## How to apply the patch (for the agent or a human reviewer)

```bash
cd scenarios/01_api_pr_update
patch -p1 < pr/add-region-and-max-results.patch
```
