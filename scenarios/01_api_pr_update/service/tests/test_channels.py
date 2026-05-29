"""Tests for GET /channels/{channel_id}.

Conventions (see skills/api-qa-conventions/SKILL.md).
"""

from __future__ import annotations

import httpx
import respx


def test_channels_known_id_returns_channel(client, known_channel_id):
    response = client.get(f"/channels/{known_channel_id}")

    assert response.status_code == 200
    body = response.json()
    assert body["channelId"] == known_channel_id
    assert body["title"]
    assert isinstance(body["subscriberCount"], int) and body["subscriberCount"] >= 0
    assert isinstance(body["videoCount"], int) and body["videoCount"] >= 0


def test_channels_unknown_id_returns_404(client):
    response = client.get("/channels/UCAAAAAAAAAAAAAAAAAAAAAA")

    assert response.status_code == 404


@respx.mock
def test_channels_upstream_5xx_returns_502(client, youtube_api_key, known_channel_id):
    respx.get("https://www.googleapis.com/youtube/v3/channels").mock(
        return_value=httpx.Response(503),
    )

    response = client.get(f"/channels/{known_channel_id}")

    assert response.status_code == 502
