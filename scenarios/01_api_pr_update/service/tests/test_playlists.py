"""Tests for GET /playlists/{playlist_id}.

Test plan (see skills/api-qa-conventions/SKILL.md — error-path coverage table):

1. Happy path — known playlist ID returns 200 with correct shape and values.
2. Unknown playlist ID — upstream returns empty items → 404.
3. Upstream 5xx — wrapper returns 502.
4. Upstream 403 (quota/key rejection) — wrapper returns 502.

The service under test is the FastAPI wrapper in service/app.py.
The third-party YouTube Data API is called for real in tests 1 and 2;
tests 3 and 4 use respx to mock the upstream without touching real network.

Conventions (see skills/api-qa-conventions/SKILL.md):
- Three-block test shape: act → assert status → assert shape and content.
- All fixtures declare scope= explicitly.
- Missing API key causes skip, not failure (handled in conftest.py).
"""

from __future__ import annotations

import httpx
import respx


# A known-stable public playlist from YouTube Spotlight (UCBR8-60-B28hp2BmDPdntcQ).
# This playlist has been present for years and is unlikely to be removed.
KNOWN_PLAYLIST_ID = "PLbpi6ZahtOH7cjq5ua8vGj9CKfIfi921X"

# A playlist-shaped ID that the YouTube API will return as empty items.
UNKNOWN_PLAYLIST_ID = "PLaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa"


# -----------------------------------------------------------------------------
# Happy path
# -----------------------------------------------------------------------------

def test_playlists_known_id_returns_playlist(client):
    response = client.get(f"/playlists/{KNOWN_PLAYLIST_ID}")

    assert response.status_code == 200
    body = response.json()
    assert body["playlistId"] == KNOWN_PLAYLIST_ID
    assert body["title"]
    assert body["channelTitle"]
    assert "description" in body
    assert isinstance(body["itemCount"], int) and body["itemCount"] >= 0


# -----------------------------------------------------------------------------
# Not-found path
# -----------------------------------------------------------------------------

def test_playlists_unknown_id_returns_404(client):
    response = client.get(f"/playlists/{UNKNOWN_PLAYLIST_ID}")

    assert response.status_code == 404
    assert "not found" in response.json()["detail"].lower()


# -----------------------------------------------------------------------------
# Upstream failure paths (mocked with respx — see api-qa-conventions skill)
# -----------------------------------------------------------------------------

@respx.mock
def test_playlists_upstream_5xx_returns_502(client, youtube_api_key):
    respx.get("https://www.googleapis.com/youtube/v3/playlists").mock(
        return_value=httpx.Response(503),
    )

    response = client.get(f"/playlists/{KNOWN_PLAYLIST_ID}")

    assert response.status_code == 502


@respx.mock
def test_playlists_upstream_quota_exceeded_returns_502(client, youtube_api_key):
    respx.get("https://www.googleapis.com/youtube/v3/playlists").mock(
        return_value=httpx.Response(403, json={"error": "quotaExceeded"}),
    )

    response = client.get(f"/playlists/{KNOWN_PLAYLIST_ID}")

    assert response.status_code == 502
