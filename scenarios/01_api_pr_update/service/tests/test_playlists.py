"""Tests for GET /playlists/{playlist_id}.

Test plan (per skills/api-qa-conventions/SKILL.md error-path coverage table):

  1. test_playlists_known_id_returns_playlist
     - Happy path: real playlist ID returns 200 with correct shape and populated values.

  2. test_playlists_unknown_id_returns_404
     - Synthetic but structurally valid ID that maps to no playlist → 404.

  3. test_playlists_upstream_5xx_returns_502
     - Upstream YouTube API returns 503 → wrapper returns 502 (mocked with respx).

  4. test_playlists_upstream_403_returns_502
     - Upstream YouTube API returns 403 (quota exceeded) → wrapper returns 502.
"""

from __future__ import annotations

import httpx
import respx


def test_playlists_known_id_returns_playlist(client, known_playlist_id):
    response = client.get(f"/playlists/{known_playlist_id}")

    assert response.status_code == 200
    body = response.json()
    assert body["playlistId"] == known_playlist_id
    assert body["title"]
    assert isinstance(body["description"], str)
    assert body["channelTitle"]
    assert isinstance(body["itemCount"], int) and body["itemCount"] >= 0


def test_playlists_unknown_id_returns_404(client):
    response = client.get("/playlists/PLaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa")

    assert response.status_code == 404


@respx.mock
def test_playlists_upstream_5xx_returns_502(client, youtube_api_key, known_playlist_id):
    respx.get("https://www.googleapis.com/youtube/v3/playlists").mock(
        return_value=httpx.Response(503),
    )

    response = client.get(f"/playlists/{known_playlist_id}")

    assert response.status_code == 502


@respx.mock
def test_playlists_upstream_403_returns_502(client, youtube_api_key, known_playlist_id):
    respx.get("https://www.googleapis.com/youtube/v3/playlists").mock(
        return_value=httpx.Response(403),
    )

    response = client.get(f"/playlists/{known_playlist_id}")

    assert response.status_code == 502
