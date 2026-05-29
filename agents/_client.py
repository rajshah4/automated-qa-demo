"""Minimal V1 Conversation API client for the demo.

Why this exists:
- The agents/ scripts need to POST to /api/v1/app-conversations on the
  OpenHands platform. That's a ~50-line job; we don't want to take a
  dependency on a larger client just for that.
- The full reference client lives in skills/openhands-api/scripts/openhands_api.py
  if you ever need fancy features (event streaming, sandbox lifecycle, etc.).
  Use that if you outgrow this.

Auth: Bearer header, OPENHANDS_API_KEY from env (or OPENHANDS_CLOUD_API_KEY).
Base URL: defaults to https://app.all-hands.dev — override with OPENHANDS_BASE_URL.
"""

from __future__ import annotations

import os
import time
from typing import Any

import httpx


class OpenHandsClient:
    def __init__(
        self,
        *,
        api_key: str | None = None,
        base_url: str | None = None,
        timeout: float = 120.0,
    ) -> None:
        api_key = (
            api_key
            or os.environ.get("OPENHANDS_API_KEY")
            or os.environ.get("OPENHANDS_CLOUD_API_KEY")
        )
        if not api_key:
            raise RuntimeError(
                "OPENHANDS_API_KEY is not set. Add it to .env or export it.",
            )
        self._base_url = (
            base_url or os.environ.get("OPENHANDS_BASE_URL") or "https://app.all-hands.dev"
        ).rstrip("/")
        self._client = httpx.Client(
            base_url=self._base_url,
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
                "Accept": "application/json",
            },
            timeout=timeout,
        )

    # -------------------------------------------------------------------------
    # Conversations
    # -------------------------------------------------------------------------

    def start_conversation(
        self,
        *,
        initial_message: str,
        selected_repository: str | None = None,
        selected_branch: str | None = None,
        title: str | None = None,
    ) -> dict[str, Any]:
        """POST /api/v1/app-conversations — start a conversation."""
        payload: dict[str, Any] = {
            "initial_message": {
                "role": "user",
                "content": [{"type": "text", "text": initial_message}],
                "run": True,
            }
        }
        if selected_repository:
            payload["selected_repository"] = selected_repository
        if selected_branch:
            payload["selected_branch"] = selected_branch
        if title:
            payload["title"] = title

        response = self._client.post("/api/v1/app-conversations", json=payload)
        response.raise_for_status()
        return response.json()

    def get_conversation(self, app_conversation_id: str) -> dict[str, Any] | None:
        """GET /api/v1/app-conversations?ids=<id> — fetch a single conversation."""
        response = self._client.get(
            "/api/v1/app-conversations",
            params={"ids": app_conversation_id},
        )
        response.raise_for_status()
        body = response.json()
        items = body if isinstance(body, list) else body.get("items") or []
        return items[0] if items else None

    def wait_until_finished(
        self,
        app_conversation_id: str,
        *,
        interval_seconds: float = 5.0,
        max_seconds: float = 1800.0,
    ) -> dict[str, Any]:
        """Poll a conversation until `execution_status` is a terminal state.

        Terminal states observed in the V1 API: 'finished', 'failed',
        'stopped', 'cancelled'. Anything else is treated as still running.
        """
        terminal = {"finished", "failed", "stopped", "cancelled"}
        deadline = time.monotonic() + max_seconds
        while True:
            conv = self.get_conversation(app_conversation_id)
            if conv and (conv.get("execution_status") or "").lower() in terminal:
                return conv
            if time.monotonic() >= deadline:
                raise TimeoutError(
                    f"Conversation {app_conversation_id} did not reach a "
                    f"terminal state within {max_seconds:.0f}s.",
                )
            time.sleep(interval_seconds)

    def get_start_task(self, task_id: str) -> dict[str, Any] | None:
        """GET /api/v1/app-conversations/start-tasks?ids=<task_id>

        Returns a list of task dicts (one per id queried), or None if the
        list is empty. We always query for a single id, so this returns the
        first element when present.
        """
        response = self._client.get(
            "/api/v1/app-conversations/start-tasks",
            params={"ids": task_id},
        )
        response.raise_for_status()
        body = response.json()
        # Endpoint returns a bare list; some deployments wrap it in {"items": [...]}.
        items = body if isinstance(body, list) else body.get("items") or []
        return items[0] if items else None

    def poll_until_ready(
        self,
        task_id: str,
        *,
        interval_seconds: float = 2.0,
        max_seconds: float = 120.0,
    ) -> dict[str, Any]:
        """Poll the start-task endpoint until `app_conversation_id` appears."""
        deadline = time.monotonic() + max_seconds
        while True:
            task = self.get_start_task(task_id)
            if task and task.get("app_conversation_id"):
                return task
            if time.monotonic() >= deadline:
                raise TimeoutError(
                    f"Start task {task_id} did not produce an app_conversation_id "
                    f"within {max_seconds:.0f}s.",
                )
            time.sleep(interval_seconds)

    # -------------------------------------------------------------------------
    # Convenience
    # -------------------------------------------------------------------------

    def conversation_url(self, app_conversation_id: str) -> str:
        return f"{self._base_url}/conversations/{app_conversation_id}"

    def close(self) -> None:
        self._client.close()

    def __enter__(self) -> OpenHandsClient:
        return self

    def __exit__(self, *exc: object) -> None:
        self.close()
