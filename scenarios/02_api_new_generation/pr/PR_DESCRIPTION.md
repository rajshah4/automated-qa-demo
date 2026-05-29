# PR: Add `/playlists/{playlist_id}` endpoint

## Summary

Adds a new endpoint that returns details for a YouTube playlist by ID. The
endpoint proxies the YouTube Data API v3 `playlists.list` call and
normalizes the response.

**Endpoint:** `GET /playlists/{playlist_id}`

**Response shape:**

```json
{
  "playlistId": "PLrAXtmErZgOeiKm4sgNOknGvNjby9efdf",
  "title": "Example Playlist",
  "description": "...",
  "channelTitle": "Some Channel",
  "itemCount": 42
}
```

**Error responses:**

- `404` if the playlist ID does not exist (upstream returns empty `items`)
- `502` if the upstream YouTube API is unreachable or returns 5xx / 403

## Why

A consumer team needs to display playlist metadata next to embedded videos.
This is the smallest endpoint that satisfies that need without bringing in
the full playlist-items API (that's a separate PR).

## Test plan

**No tests are included in this PR.** The QA agent should generate the test
suite from scratch following the `api-qa-conventions` skill.

Expected coverage (per the skill's error-path table):

| Scenario | Expected status |
|---|---|
| Known playlist ID | 200 |
| Unknown playlist ID | 404 |
| Empty playlist ID (path) | 404 (FastAPI route mismatch) |
| Upstream 5xx | 502 |
| Upstream 403 (quota) | 502 |

The new test file should be at `service/tests/test_playlists.py` and should
follow the three-block shape (act → assert status → assert shape/content)
used by the existing test files.

## How to apply

```bash
cd scenarios/01_api_pr_update
patch -p1 < ../02_api_new_generation/pr/add-playlists-endpoint.patch
```
