"""Tests for GET /search.

Conventions (see skills/api-qa-conventions/SKILL.md):
- One file per endpoint group.
- Three-block test shape: act → assert status → assert shape and content.
- Error-path coverage table: happy path, missing required param, upstream failure.
"""

from __future__ import annotations

import httpx
import respx


# -----------------------------------------------------------------------------
# Happy path
# -----------------------------------------------------------------------------

def test_search_default_params_returns_results(client):
    response = client.get("/search", params={"q": "openhands"})

    assert response.status_code == 200
    body = response.json()
    assert "items" in body
    assert len(body["items"]) > 0
    # Every item exposes the normalized wrapper shape — not the raw YT shape.
    for item in body["items"]:
        assert set(item.keys()) == {"videoId", "title", "channelTitle", "publishedAt"}
        assert item["videoId"]
        assert item["title"]


# -----------------------------------------------------------------------------
# Validation
# -----------------------------------------------------------------------------

def test_search_missing_query_param_returns_422(client):
    # FastAPI returns 422 for missing required query params (Pydantic validation).
    response = client.get("/search")

    assert response.status_code == 422


def test_search_empty_query_param_returns_422(client):
    response = client.get("/search", params={"q": ""})

    assert response.status_code == 422


# -----------------------------------------------------------------------------
# Upstream failure paths (mocked with respx — see api-qa-conventions skill)
# -----------------------------------------------------------------------------

@respx.mock
def test_search_upstream_5xx_returns_502(client, youtube_api_key):
    respx.get("https://www.googleapis.com/youtube/v3/search").mock(
        return_value=httpx.Response(503, json={"error": "upstream down"}),
    )

    response = client.get("/search", params={"q": "openhands"})

    assert response.status_code == 502
    assert "Upstream YouTube API failure" in response.json()["detail"]


@respx.mock
def test_search_upstream_quota_exceeded_returns_502(client, youtube_api_key):
    respx.get("https://www.googleapis.com/youtube/v3/search").mock(
        return_value=httpx.Response(403, json={"error": "quotaExceeded"}),
    )

    response = client.get("/search", params={"q": "openhands"})

    assert response.status_code == 502


# -----------------------------------------------------------------------------
# New parameters: regionCode and maxResults — happy paths
# -----------------------------------------------------------------------------

def test_search_with_region_code_returns_results(client):
    response = client.get("/search", params={"q": "football", "regionCode": "US"})

    assert response.status_code == 200
    body = response.json()
    assert "items" in body
    assert len(body["items"]) > 0
    for item in body["items"]:
        assert set(item.keys()) == {"videoId", "title", "channelTitle", "publishedAt"}


def test_search_with_max_results_limits_response(client):
    response = client.get("/search", params={"q": "python tutorial", "maxResults": 10})

    assert response.status_code == 200
    body = response.json()
    assert "items" in body
    assert len(body["items"]) <= 10


def test_search_with_region_code_and_max_results_returns_results(client):
    response = client.get(
        "/search", params={"q": "music", "regionCode": "GB", "maxResults": 5}
    )

    assert response.status_code == 200
    body = response.json()
    assert "items" in body
    assert len(body["items"]) <= 5


# -----------------------------------------------------------------------------
# New parameters: regionCode and maxResults — validation
# -----------------------------------------------------------------------------

def test_search_region_code_too_long_returns_422(client):
    # "USA" is 3 letters; regionCode must be exactly 2 characters.
    response = client.get("/search", params={"q": "test", "regionCode": "USA"})

    assert response.status_code == 422


def test_search_region_code_too_short_returns_422(client):
    # "U" is 1 letter; regionCode must be exactly 2 characters.
    response = client.get("/search", params={"q": "test", "regionCode": "U"})

    assert response.status_code == 422


def test_search_max_results_zero_returns_422(client):
    # maxResults must be >= 1.
    response = client.get("/search", params={"q": "test", "maxResults": 0})

    assert response.status_code == 422


def test_search_max_results_above_limit_returns_422(client):
    # maxResults must be <= 50.
    response = client.get("/search", params={"q": "test", "maxResults": 51})

    assert response.status_code == 422
