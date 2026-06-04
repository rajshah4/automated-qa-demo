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

## How to apply the patch (for the agent or a human reviewer)

```bash
cd scenarios/01_api_pr_update
patch -p1 < pr/add-region-and-max-results.patch
```
