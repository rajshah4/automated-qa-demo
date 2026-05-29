"""Tests for GET /videos/{video_id}.

Conventions (see skills/api-qa-conventions/SKILL.md).
"""

from __future__ import annotations

import httpx
import respx


# A known-stable video ID — YouTube's first-ever video, won't disappear.
KNOWN_VIDEO_ID = "jNQXAC9IVRw"  # "Me at the zoo"


def test_videos_known_id_returns_video(client):
    response = client.get(f"/videos/{KNOWN_VIDEO_ID}")

    assert response.status_code == 200
    body = response.json()
    assert body["videoId"] == KNOWN_VIDEO_ID
    assert body["title"]
    assert body["channelTitle"]
    assert isinstance(body["viewCount"], int) and body["viewCount"] > 0
    assert isinstance(body["likeCount"], int)


def test_videos_unknown_id_returns_404(client):
    # 11 chars of nonsense — YT will return empty items.
    response = client.get("/videos/AAAAAAAAAAA")

    assert response.status_code == 404
    assert "not found" in response.json()["detail"].lower()


@respx.mock
def test_videos_upstream_5xx_returns_502(client, youtube_api_key):
    respx.get("https://www.googleapis.com/youtube/v3/videos").mock(
        return_value=httpx.Response(503),
    )

    response = client.get(f"/videos/{KNOWN_VIDEO_ID}")

    assert response.status_code == 502
