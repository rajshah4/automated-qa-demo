"""Shared pytest fixtures for the YouTube wrapper service tests.

Conventions enforced here (see skills/api-qa-conventions/SKILL.md):
- Every fixture declares `scope=` explicitly.
- Missing external credentials cause `skip`, not failure.
- Session-scoped fixtures are read-only.
"""

from __future__ import annotations

import os

import pytest
from fastapi.testclient import TestClient

from service.app import app


@pytest.fixture(scope="session")
def youtube_api_key() -> str:
    key = os.environ.get("YOUTUBE_API_KEY")
    if not key:
        pytest.skip("YOUTUBE_API_KEY not set; skipping live API tests")
    return key


@pytest.fixture(scope="session")
def client(youtube_api_key: str) -> TestClient:
    # The wrapper service reads YOUTUBE_API_KEY from env at request time.
    # The session-scoped fixture above guarantees it's set or skips.
    return TestClient(app)


# A known-stable channel / video that won't disappear: YouTube's own channel.
KNOWN_CHANNEL_ID = "UCBR8-60-B28hp2BmDPdntcQ"  # YouTube Spotlight
KNOWN_VIDEO_QUERY = "youtube rewind 2018"

# A known-stable playlist from the YouTube Spotlight channel.
KNOWN_PLAYLIST_ID = "PLbpi6ZahtOH4vec4VIxczjwC4pY0jAPNC"  # "Knock, knock" playlist


@pytest.fixture(scope="session")
def known_channel_id() -> str:
    return KNOWN_CHANNEL_ID


@pytest.fixture(scope="session")
def known_playlist_id() -> str:
    return KNOWN_PLAYLIST_ID
