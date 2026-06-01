"""Tests for GET /playlists/{playlist_id}.

Test plan (see skills/api-qa-conventions/SKILL.md for error-path coverage table):

1. Happy path — known stable playlist returns 200 with correct response shape.
2. Unknown playlist ID returns 404.
3. Upstream 5xx returns 502 (mocked with respx).
4. Upstream quota / 403 returns 502 (mocked with respx).

Conventions (see skills/api-qa-conventions/SKILL.md):
- One file per endpoint group.
- Three-block test shape: act → assert status → assert shape and content.
- Real network calls; only upstream failures are mocked.
"""

from __future__ import annotations

import httpx
import respx


# A stable YouTube playlist from the official YouTube Music channel.
# "Popular Music Videos" — unlikely to be deleted.
KNOWN_PLAYLIST_ID = "PLFgquLnL59alCl_2TQvOiD5Vgm1hCaGSI"


# -----------------------------------------------------------------------------
# Happy path
# -----------------------------------------------------------------------------

def test_playlists_known_id_returns_playlist(client):
    response = client.get(f"/playlists/{KNOWN_PLAYLIST_ID}")

    assert response.status_code == 200
    body = response.json()
    assert set(body.keys()) == {"playlistId", "title", "description", "channelTitle", "itemCount"}
    assert body["playlistId"] == KNOWN_PLAYLIST_ID
    assert body["title"]
    assert body["channelTitle"]
    assert isinstance(body["itemCount"], int) and body["itemCount"] >= 0


# -----------------------------------------------------------------------------
# Error paths
# -----------------------------------------------------------------------------

def test_playlists_unknown_id_returns_404(client):
    response = client.get("/playlists/PLAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA")

    assert response.status_code == 404
    assert "not found" in response.json()["detail"].lower()


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
