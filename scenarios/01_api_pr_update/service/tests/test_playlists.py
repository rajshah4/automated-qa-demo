"""Tests for GET /playlists/{playlist_id}.

Test plan (see skills/api-qa-conventions/SKILL.md — error-path coverage table):

  1. test_playlists_known_id_returns_playlist
       Happy path: a stable, real playlist ID returns 200 with the expected shape.
  2. test_playlists_unknown_id_returns_404
       Unknown / nonsense playlist ID: upstream returns empty items → 404.
  3. test_playlists_upstream_5xx_returns_502
       Upstream YouTube API returns 5xx → wrapper must return 502.
  4. test_playlists_upstream_403_returns_502
       Upstream YouTube API returns 403 (quota / key rejection) → 502.

Conventions:
  - Real network calls for happy-path and 404 tests (no mocking the SUT).
  - respx mock used only where the error is hard to provoke for real (5xx, 403).
  - Never assert against raw YouTube shapes; assert against our wrapper's shape.
"""

from __future__ import annotations

import httpx
import respx

# The YouTube Spotlight channel's uploads playlist is a stable, Google-owned
# playlist that will not disappear:  "UU" + channel_id[2:]
# channel UCBR8-60-B28hp2BmDPdntcQ  →  uploads UUBR8-60-B28hp2BmDPdntcQ
KNOWN_PLAYLIST_ID = "UUBR8-60-B28hp2BmDPdntcQ"  # YouTube Spotlight uploads


def test_playlists_known_id_returns_playlist(client):
    response = client.get(f"/playlists/{KNOWN_PLAYLIST_ID}")

    assert response.status_code == 200
    body = response.json()
    assert body["playlistId"] == KNOWN_PLAYLIST_ID
    assert body["title"]
    assert body["channelTitle"]
    assert "description" in body
    assert isinstance(body["itemCount"], int) and body["itemCount"] >= 0


def test_playlists_unknown_id_returns_404(client):
    # 24-char nonsense — YouTube will return empty items.
    response = client.get("/playlists/PLAAAAAAAAAAAAAAAAAAAAAAAA")

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
def test_playlists_upstream_403_returns_502(client, youtube_api_key):
    respx.get("https://www.googleapis.com/youtube/v3/playlists").mock(
        return_value=httpx.Response(403),
    )

    response = client.get(f"/playlists/{KNOWN_PLAYLIST_ID}")

    assert response.status_code == 502
