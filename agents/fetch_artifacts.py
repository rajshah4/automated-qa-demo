"""Pull artifacts from a finished conversation's sandbox to your local disk.

What this collects, scenario-agnostic:

1. /tmp/qa-report.md            — the agent's narrative report
2. <repo>/changes.diff          — `git diff HEAD` inside the sandbox repo,
                                  i.e. exactly what the agent changed to
                                  files that were already tracked
3. <repo>/git-status.txt        — `git status --short` (lists untracked
                                  files too, so we know what to pull)
4. New untracked files under    — generated specs, recordings, fresh test
   scenarios/*/                   files, anything the agent created

Useful both locally (`python -m agents.fetch_artifacts <conversation_id>`)
and inside the CI workflow (called by .github/workflows/qa.yml).
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Any

try:
    from dotenv import load_dotenv

    load_dotenv(override=True)
except ImportError:
    pass

import httpx

from agents._client import OpenHandsClient
from agents._ci import emit as ci_emit

REPO_ROOT = Path(__file__).resolve().parent.parent


def _agent_server(conv: dict[str, Any]) -> tuple[str, str]:
    session_key = conv["session_api_key"]
    base = conv["conversation_url"].rsplit("/api/conversations", 1)[0]
    return base, session_key


def _bash(client: httpx.Client, command: str) -> str:
    """Run a bash command in the sandbox and return its stdout (never None)."""
    r = client.post("/api/bash/execute_bash_command", json={"command": command})
    r.raise_for_status()
    out = r.json() or {}
    return (out.get("stdout") or "") + (
        ("\nSTDERR:" + out["stderr"]) if out.get("stderr") else ""
    )


def _download(client: httpx.Client, abs_path: str) -> bytes | None:
    """GET /api/file/download?path=... — returns bytes or None if missing."""
    r = client.get("/api/file/download", params={"path": abs_path})
    if r.status_code == 404:
        return None
    r.raise_for_status()
    return r.content


def _save(target: Path, blob: bytes | None, src_label: str) -> None:
    if blob is None:
        print(f"  MISS  {src_label}")
        return
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_bytes(blob)
    print(f"  OK    {src_label}  →  {target.relative_to(REPO_ROOT)}  ({len(blob)} B)")


def _find_repo_path(sb: httpx.Client) -> str | None:
    """Locate the cloned repo inside the sandbox. The path varies by
    sandbox image, so we search rather than hardcoding."""
    output = _bash(
        sb,
        "find /workspace -maxdepth 3 -type d -name 'automated-qa-demo' "
        "2>/dev/null | head -1",
    )
    path = output.strip().splitlines()[0] if output.strip() else ""
    return path or None


def fetch(conversation_id: str, dest: Path) -> int:
    """Pull all artifacts. Returns the count of files saved."""
    with OpenHandsClient() as c:
        conv = c.get_conversation(conversation_id)
    if not conv:
        sys.exit(f"Conversation {conversation_id} not found.")

    agent_base, session_key = _agent_server(conv)
    print(f"Sandbox:  {agent_base}")
    print(f"Status:   {conv.get('execution_status')}")
    print(f"Dest:     {dest}")
    dest.mkdir(parents=True, exist_ok=True)
    saved = 0

    with httpx.Client(
        base_url=agent_base,
        headers={"X-Session-API-Key": session_key, "Accept": "application/json"},
        timeout=120,
    ) as sb:
        repo_path = _find_repo_path(sb)
        if not repo_path:
            print("Could not locate the repo inside the sandbox.")
            return 0
        print(f"Repo:     {repo_path}\n")

        # ---------------- /tmp/qa-report.md ----------------
        print("--- Report ---")
        blob = _download(sb, "/tmp/qa-report.md")
        _save(dest / "qa-report.md", blob, "/tmp/qa-report.md")
        if blob is not None:
            saved += 1

        # ---------------- git diff + status ----------------
        # Capture changes to tracked files (API scenarios mostly produce
        # diffs to existing test files), plus a list of new files.
        print("\n--- Git changes ---")
        diff = _bash(sb, f"cd {repo_path} && git diff HEAD")
        (dest / "changes.diff").write_text(diff, encoding="utf-8")
        print(f"  OK    git diff HEAD  →  changes.diff  ({len(diff)} B)")
        saved += 1

        status = _bash(sb, f"cd {repo_path} && git status --short")
        (dest / "git-status.txt").write_text(status, encoding="utf-8")
        print(f"  OK    git status     →  git-status.txt  ({len(status)} B)")
        saved += 1

        # ---------------- Untracked files under scenarios/ ----------------
        # These are files the agent created from scratch (e.g. UI specs,
        # recordings, brand-new test_*.py files). We list them and pull
        # each one. .gitkeep placeholders are skipped.
        print("\n--- New artifacts under scenarios/ ---")
        new_files = _bash(
            sb,
            f"cd {repo_path} && "
            "git ls-files --others --exclude-standard scenarios/ | "
            "grep -v '/.gitkeep$' || true",
        ).strip()
        if not new_files:
            print("  (none)")
        else:
            for rel in new_files.splitlines():
                rel = rel.strip()
                if not rel:
                    continue
                blob = _download(sb, f"{repo_path}/{rel}")
                _save(dest / rel, blob, rel)
                if blob is not None:
                    saved += 1

        # ---------------- runs.jsonl, in case it accumulated rows ----------
        print("\n--- runs.jsonl (if present) ---")
        blob = _download(sb, f"{repo_path}/runs.jsonl")
        _save(dest / "runs.jsonl", blob, "runs.jsonl")
        if blob is not None:
            saved += 1

    print(f"\nSaved {saved} files to {dest}")
    return saved


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("conversation_id")
    p.add_argument(
        "--dest",
        default=None,
        help="Local directory to download into. "
        "Defaults to ./artifacts/<conversation_id>/.",
    )
    args = p.parse_args()

    dest = (
        Path(args.dest).resolve()
        if args.dest
        else REPO_ROOT / "artifacts" / args.conversation_id
    )
    saved = fetch(args.conversation_id, dest)
    ci_emit("artifacts_dir", str(dest))
    ci_emit("artifacts_count", str(saved))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
