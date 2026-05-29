"""Per-run timing / cost log for QA conversations.

Records one JSON line per conversation in `runs.jsonl` at the repo root.
Each row captures: when it ran, which scenario, how long it took, how much
it cost, and the conversation URL.

CLI:
    python -m agents.runs log <conversation_id> [--scenario PATH] [--wait]
        Refresh or insert a row for the given conversation. With --wait,
        poll until the conversation reaches a terminal state first.

    python -m agents.runs view [--limit N]
        Print a table of recent runs.

The starter scripts call `log_run()` automatically on kickoff and again
(in --wait mode) after the conversation finishes. So the typical user
never invokes this module directly — it's there for backfills, ad-hoc
inspection, and as a building block.
"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

try:
    from dotenv import load_dotenv

    load_dotenv(override=True)
except ImportError:
    pass

from agents._client import OpenHandsClient

REPO_ROOT = Path(__file__).resolve().parent.parent
RUNS_PATH = REPO_ROOT / "runs.jsonl"


# -----------------------------------------------------------------------------
# Pure helpers
# -----------------------------------------------------------------------------


def _parse_iso(ts: str | None) -> datetime | None:
    if not ts:
        return None
    # API returns trailing 'Z' which fromisoformat handles only on 3.11+.
    return datetime.fromisoformat(ts.replace("Z", "+00:00"))


def _duration_seconds(conv: dict[str, Any]) -> float | None:
    start = _parse_iso(conv.get("created_at"))
    end = _parse_iso(conv.get("updated_at"))
    if not start or not end:
        return None
    return (end - start).total_seconds()


def _row_from_conversation(
    conv: dict[str, Any], *, scenario: str | None = None
) -> dict[str, Any]:
    metrics = conv.get("metrics") or {}
    tokens = metrics.get("accumulated_token_usage") or {}
    return {
        "logged_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "conversation_id": conv.get("id"),
        "scenario": scenario,
        "title": conv.get("title"),
        "selected_repository": conv.get("selected_repository"),
        "selected_branch": conv.get("selected_branch"),
        "llm_model": conv.get("llm_model"),
        "execution_status": conv.get("execution_status"),
        "created_at": conv.get("created_at"),
        "updated_at": conv.get("updated_at"),
        "duration_seconds": _duration_seconds(conv),
        "cost_usd": metrics.get("accumulated_cost"),
        "prompt_tokens": tokens.get("prompt_tokens"),
        "completion_tokens": tokens.get("completion_tokens"),
        "cache_read_tokens": tokens.get("cache_read_tokens"),
        "cache_write_tokens": tokens.get("cache_write_tokens"),
        "url": f"https://app.all-hands.dev/conversations/{conv.get('id')}",
    }


def _read_rows() -> list[dict[str, Any]]:
    if not RUNS_PATH.is_file():
        return []
    rows: list[dict[str, Any]] = []
    for line in RUNS_PATH.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line:
            continue
        rows.append(json.loads(line))
    return rows


def _write_rows(rows: list[dict[str, Any]]) -> None:
    RUNS_PATH.write_text(
        "\n".join(json.dumps(r) for r in rows) + ("\n" if rows else ""),
        encoding="utf-8",
    )


def _upsert(row: dict[str, Any]) -> None:
    """Insert or replace a row keyed on conversation_id."""
    conv_id = row["conversation_id"]
    rows = [r for r in _read_rows() if r.get("conversation_id") != conv_id]
    rows.append(row)
    _write_rows(rows)


# -----------------------------------------------------------------------------
# Public API used by the starter scripts
# -----------------------------------------------------------------------------


def log_run(
    conversation_id: str,
    *,
    scenario: str | None = None,
    wait: bool = False,
    client: OpenHandsClient | None = None,
) -> dict[str, Any]:
    """Fetch a conversation and append/refresh its row in runs.jsonl.

    When `wait=True`, polls until the conversation reaches a terminal
    state before snapshotting metrics. Otherwise, snapshots whatever the
    current state is — useful right after kickoff so the row exists.
    """
    own_client = client is None
    client = client or OpenHandsClient()
    try:
        if wait:
            conv = client.wait_until_finished(conversation_id)
        else:
            conv = client.get_conversation(conversation_id)
        if not conv:
            raise RuntimeError(f"Conversation {conversation_id} not found.")
        row = _row_from_conversation(conv, scenario=scenario)
        _upsert(row)
        return row
    finally:
        if own_client:
            client.close()


# -----------------------------------------------------------------------------
# CLI
# -----------------------------------------------------------------------------


def _format_seconds(seconds: float | None) -> str:
    if seconds is None:
        return "—"
    m, s = divmod(int(seconds), 60)
    return f"{m:d}m {s:02d}s"


def _format_cost(cost: float | None) -> str:
    if cost is None:
        return "—"
    return f"${cost:.4f}"


def _cmd_log(args: argparse.Namespace) -> int:
    row = log_run(
        args.conversation_id,
        scenario=args.scenario,
        wait=args.wait,
    )
    print(
        f"{row['conversation_id']}  "
        f"{row.get('execution_status'):>10s}  "
        f"{_format_seconds(row.get('duration_seconds'))}  "
        f"{_format_cost(row.get('cost_usd'))}  "
        f"{row.get('scenario') or '—'}"
    )
    return 0


def _cmd_view(args: argparse.Namespace) -> int:
    rows = _read_rows()
    if args.scenario:
        rows = [r for r in rows if (r.get("scenario") or "").startswith(args.scenario)]
    rows.sort(key=lambda r: r.get("created_at") or "")
    rows = rows[-args.limit :] if args.limit else rows

    if not rows:
        print("No runs logged yet.")
        return 0

    header = f"{'scenario':32s}  {'status':>10s}  {'duration':>10s}  {'cost':>10s}  url"
    print(header)
    print("-" * len(header))
    for r in rows:
        scenario = (r.get("scenario") or "—")[:32]
        status = r.get("execution_status") or "—"
        duration = _format_seconds(r.get("duration_seconds"))
        cost = _format_cost(r.get("cost_usd"))
        url = r.get("url") or ""
        print(f"{scenario:32s}  {status:>10s}  {duration:>10s}  {cost:>10s}  {url}")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="cmd", required=True)

    p_log = sub.add_parser("log", help="Insert or refresh a run row")
    p_log.add_argument("conversation_id")
    p_log.add_argument("--scenario", default=None)
    p_log.add_argument(
        "--wait",
        action="store_true",
        help="Poll until the conversation reaches a terminal state before logging.",
    )
    p_log.set_defaults(func=_cmd_log)

    p_view = sub.add_parser("view", help="Print recent runs")
    p_view.add_argument("--limit", type=int, default=20)
    p_view.add_argument(
        "--scenario",
        default=None,
        help="Only show rows whose scenario starts with this string.",
    )
    p_view.set_defaults(func=_cmd_view)

    args = parser.parse_args()
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
