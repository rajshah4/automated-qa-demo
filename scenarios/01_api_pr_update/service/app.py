"""
A small wrapper around the YouTube Data API v3.

Why this exists in the demo:
- It's a realistic shape: a FastAPI service that proxies a real third-party
  API, normalizes responses, and adds its own validation. This is the kind
  of service a QA team actually has to test.
- It's small enough that the whole surface area is visible at a glance.
- It hits real network (when YOUTUBE_API_KEY is set) so the tests are
  integration tests, not unit tests against mocks.
"""

from __future__ import annotations

import os
from typing import Any

import httpx
from fastapi import FastAPI, HTTPException, Query

YOUTUBE_API_BASE = "https://www.googleapis.com/youtube/v3"

app = FastAPI(
    title="YouTube Wrapper Service",
    description="Demo service: wraps the YouTube Data API v3 with a simpler interface.",
    version="0.1.0",
)


def _api_key() -> str:
    key = os.environ.get("YOUTUBE_API_KEY")
    if not key:
        raise HTTPException(
            status_code=503,
            detail="YOUTUBE_API_KEY is not configured on the server.",
        )
    return key


def _call_youtube(path: str, params: dict[str, Any]) -> dict[str, Any]:
    """Single chokepoint for upstream calls — easy to mock with respx in tests."""
    params = {**params, "key": _api_key()}
    try:
        response = httpx.get(f"{YOUTUBE_API_BASE}{path}", params=params, timeout=10.0)
    except httpx.HTTPError as exc:
        raise HTTPException(status_code=502, detail=f"Upstream YouTube API unreachable: {exc}")

    if response.status_code >= 500:
        raise HTTPException(status_code=502, detail="Upstream YouTube API failure")
    if response.status_code == 403:
        raise HTTPException(status_code=502, detail="Upstream YouTube API rejected the key or quota")
    if response.status_code >= 400:
        # Surface 4xx as 400 to the caller — their request was bad.
        raise HTTPException(status_code=400, detail=response.json())

    return response.json()


# -----------------------------------------------------------------------------
# /search
# -----------------------------------------------------------------------------

@app.get("/search")
def search(
    q: str = Query(..., min_length=1, description="Search query"),
) -> dict[str, Any]:
    """
    Search YouTube for videos matching `q`.

    Returns a normalized response shape — callers should not depend on the
    raw YouTube response.
    """
    upstream = _call_youtube(
        "/search",
        {"q": q, "part": "snippet", "type": "video"},
    )

    return {
        "items": [
            {
                "videoId": item["id"]["videoId"],
                "title": item["snippet"]["title"],
                "channelTitle": item["snippet"]["channelTitle"],
                "publishedAt": item["snippet"]["publishedAt"],
            }
            for item in upstream.get("items", [])
            if item.get("id", {}).get("videoId")
        ],
    }


# -----------------------------------------------------------------------------
# /videos/{video_id}
# -----------------------------------------------------------------------------

@app.get("/videos/{video_id}")
def get_video(video_id: str) -> dict[str, Any]:
    """Get details for a single video by ID."""
    upstream = _call_youtube(
        "/videos",
        {"id": video_id, "part": "snippet,statistics"},
    )

    items = upstream.get("items", [])
    if not items:
        raise HTTPException(status_code=404, detail=f"Video {video_id!r} not found")

    item = items[0]
    snippet = item["snippet"]
    stats = item.get("statistics", {})
    return {
        "videoId": item["id"],
        "title": snippet["title"],
        "description": snippet["description"],
        "channelTitle": snippet["channelTitle"],
        "viewCount": int(stats.get("viewCount", 0)),
        "likeCount": int(stats.get("likeCount", 0)),
    }


# -----------------------------------------------------------------------------
# /channels/{channel_id}
# -----------------------------------------------------------------------------

@app.get("/channels/{channel_id}")
def get_channel(channel_id: str) -> dict[str, Any]:
    """Get details for a single channel by ID."""
    upstream = _call_youtube(
        "/channels",
        {"id": channel_id, "part": "snippet,statistics"},
    )

    items = upstream.get("items", [])
    if not items:
        raise HTTPException(status_code=404, detail=f"Channel {channel_id!r} not found")

    item = items[0]
    snippet = item["snippet"]
    stats = item.get("statistics", {})
    return {
        "channelId": item["id"],
        "title": snippet["title"],
        "description": snippet["description"],
        "subscriberCount": int(stats.get("subscriberCount", 0)),
        "videoCount": int(stats.get("videoCount", 0)),
    }


# -----------------------------------------------------------------------------
# /playlists/{playlist_id}
# -----------------------------------------------------------------------------

@app.get("/playlists/{playlist_id}")
def get_playlist(playlist_id: str) -> dict[str, Any]:
    """Get details for a single playlist by ID."""
    upstream = _call_youtube(
        "/playlists",
        {"id": playlist_id, "part": "snippet,contentDetails"},
    )

    items = upstream.get("items", [])
    if not items:
        raise HTTPException(status_code=404, detail=f"Playlist {playlist_id!r} not found")

    item = items[0]
    snippet = item["snippet"]
    content_details = item.get("contentDetails", {})
    return {
        "playlistId": item["id"],
        "title": snippet["title"],
        "description": snippet["description"],
        "channelTitle": snippet["channelTitle"],
        "itemCount": int(content_details.get("itemCount", 0)),
    }
