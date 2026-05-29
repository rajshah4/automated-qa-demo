"""Pull artifacts from a finished conversation's sandbox to your local disk.

Useful when the agent's output (generated specs, recordings, reports) lives
inside the sandbox and you want to inspect or commit it locally.

CLI:
    python -m agents.fetch_artifacts <conversation_id> [--dest PATH]

Default dest is `./artifacts/<conversation_id>/`.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

try:
    from dotenv import load_dotenv

    load_dotenv(override=True)
except ImportError:
    pass

import httpx

from agents._client import OpenHandsClient

REPO_ROOT = Path(__file__).resolve().parent.parent


def _agent_server(conv: dict) -> tuple[str, str]:
    session_key = conv["session_api_key"]
    base = conv["conversation_url"].rsplit("/api/conversations", 1)[0]
    return base, session_key


def _bash(client: httpx.Client, command: str) -> dict:
    r = client.post("/api/bash/execute_bash_command", json={"command": command})
    r.raise_for_status()
    return r.json()


def _download_bytes(client: httpx.Client, abs_path: str) -> bytes | None:
    """Download a file from the sandbox. Returns None if missing.

    The agent server expects the path as a query param, not a URL path
    segment: GET /api/file/download?path=/abs/path/to/file
    """
    r = client.get("/api/file/download", params={"path": abs_path})
    if r.status_code == 404:
        return None
    r.raise_for_status()
    return r.content


def fetch(conversation_id: str, dest: Path) -> None:
    with OpenHandsClient() as c:
        conv = c.get_conversation(conversation_id)
    if not conv:
        sys.exit(f"Conversation {conversation_id} not found.")

    agent_base, session_key = _agent_server(conv)
    print(f"Sandbox:  {agent_base}")
    print(f"Status:   {conv.get('execution_status')}")
    print(f"Dest:     {dest}")
    dest.mkdir(parents=True, exist_ok=True)

    with httpx.Client(
        base_url=agent_base,
        headers={"X-Session-API-Key": session_key, "Accept": "application/json"},
        timeout=120,
    ) as sb:
        # 1. Locate the workspace root (varies by sandbox image).
        pwd = _bash(sb, "echo WS=$PWD; ls /workspace 2>/dev/null | head; ls / 2>/dev/null | head")
        print("\n--- Sandbox probe ---")
        print(pwd.get("stdout", ""))
        if pwd.get("stderr"):
            print("stderr:", pwd["stderr"][:200])

        # 2. Find candidate files: report, generated specs, recordings.
        targets = _bash(
            sb,
            "ls -la /tmp/qa-report.md 2>/dev/null; "
            "find / -maxdepth 6 -type d -name 'generated_specs' 2>/dev/null; "
            "find / -maxdepth 6 -type d -name 'recordings' 2>/dev/null",
        )
        print("\n--- Targets ---")
        print(targets.get("stdout", ""))

        # 3. Try a known common workspace path; the agent works in
        #    /workspace/<repo-name>. Fall back to a find if needed.
        listing = _bash(
            sb,
            "REPO=$(find /workspace -maxdepth 2 -type d -name 'automated-qa-demo' 2>/dev/null | head -1); "
            "echo REPO=$REPO; "
            "ls -la $REPO/scenarios/03_ui_workflow/generated_specs $REPO/scenarios/03_ui_workflow/recordings 2>/dev/null",
        )
        print("\n--- Scenario 3 contents ---")
        print(listing.get("stdout", ""))

        # Derive the repo path from the probe output.
        repo_path = None
        for line in listing.get("stdout", "").splitlines():
            if line.startswith("REPO="):
                repo_path = line.split("=", 1)[1].strip() or None
                break
        if not repo_path:
            print("Could not locate repo in sandbox; aborting download.")
            return

        # 4. Download the report and any spec/recording files.
        wanted = [
            ("/tmp/qa-report.md", dest / "qa-report.md"),
        ]
        specs_dir = f"{repo_path}/scenarios/03_ui_workflow/generated_specs"
        recordings_dir = f"{repo_path}/scenarios/03_ui_workflow/recordings"

        for sandbox_dir, local_dir_name in (
            (specs_dir, "generated_specs"),
            (recordings_dir, "recordings"),
        ):
            names = _bash(sb, f"ls -1 {sandbox_dir} 2>/dev/null")
            for name in names.get("stdout", "").splitlines():
                name = name.strip()
                if not name or name == ".gitkeep":
                    continue
                wanted.append(
                    (f"{sandbox_dir}/{name}", dest / local_dir_name / name),
                )

        print(f"\n--- Downloading {len(wanted)} files ---")
        for src, target in wanted:
            target.parent.mkdir(parents=True, exist_ok=True)
            blob = _download_bytes(sb, src)
            if blob is None:
                print(f"  MISS  {src}")
                continue
            target.write_bytes(blob)
            print(f"  OK    {src}  →  {target.relative_to(REPO_ROOT)} ({len(blob)} bytes)")


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
    fetch(args.conversation_id, dest)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
