"""Conversation-starter for API QA scenarios.

Runs OUTSIDE the OpenHands sandbox. Builds a self-contained task prompt
from a scenario folder and POSTs it to /api/v1/app-conversations on the
OpenHands platform. The conversation that gets started then does the
actual QA work inside its own sandbox, where this repo is cloned and the
skills auto-load via AGENTS.md.

Usage:
    python -m agents.api_qa_agent --scenario scenarios/01_api_pr_update
    python -m agents.api_qa_agent --scenario scenarios/02_api_new_generation
"""

from __future__ import annotations

import argparse
import os
import sys
import textwrap
from pathlib import Path

# Load .env early so the client can read OPENHANDS_API_KEY etc.
try:
    from dotenv import load_dotenv

    # override=True so .env wins over stale shell env vars (e.g. an empty
    # DEMO_REPO left over from a previous `set -a; . ./.env` session).
    load_dotenv(override=True)
except ImportError:
    # python-dotenv is optional; if it's not installed, fall back to plain env.
    pass

from agents._client import OpenHandsClient

REPO_ROOT = Path(__file__).resolve().parent.parent


def _read_text(path: Path) -> str:
    if not path.is_file():
        sys.exit(f"Expected file does not exist: {path.relative_to(REPO_ROOT)}")
    return path.read_text(encoding="utf-8")


def _find_first(folder: Path, suffix: str) -> Path | None:
    matches = sorted(folder.glob(f"*{suffix}"))
    return matches[0] if matches else None


def _build_prompt(scenario_dir: Path) -> str:
    """Construct a self-contained task prompt for the API QA conversation."""
    scenario_rel = scenario_dir.relative_to(REPO_ROOT)
    pr_dir = scenario_dir / "pr"
    if not pr_dir.is_dir():
        sys.exit(f"Scenario {scenario_rel} has no pr/ folder.")

    pr_description_path = pr_dir / "PR_DESCRIPTION.md"
    patch_path = _find_first(pr_dir, ".patch")
    if patch_path is None:
        sys.exit(f"Scenario {scenario_rel} has no *.patch file in pr/.")

    pr_description = _read_text(pr_description_path)
    patch_rel = patch_path.relative_to(REPO_ROOT)
    pr_description_rel = pr_description_path.relative_to(REPO_ROOT)

    # The wrapper service for both API scenarios lives in scenario 01.
    # The agent will work on that service in both cases.
    service_dir_rel = Path("scenarios/01_api_pr_update")

    return textwrap.dedent(
        f"""\
        You are the API QA agent for the automated-qa-demo repo.

        ## Your task

        A PR has been opened for this scenario: `{scenario_rel}`.

        1. Read `AGENTS.md` at the repo root for general project guidance.
        2. Read the skill at `skills/api-qa-conventions/SKILL.md`. **You must
           follow it.** It is the source of truth for how tests are written
           in this repo.
        3. Read the PR description at `{pr_description_rel}` to understand
           what the PR is trying to accomplish.
        4. Read the patch at `{patch_rel}` to see the exact diff.

        ## What to do

        a. `cd` into `{service_dir_rel}`.
        b. Install dependencies: `uv venv && uv pip install -e ".[test]"`.
           If `uv` is not available, use `python -m venv .venv && source
           .venv/bin/activate && pip install -e ".[test]"`.
        c. Apply the patch from `{patch_rel}`:
           `patch -p1 < ../../{patch_rel}` (the patch is relative to the
           service folder root).
        d. Decide whether you are in the "update existing tests" path or the
           "generate tests for a brand-new endpoint" path. The PR description
           tells you which one. Follow the matching section of the
           api-qa-conventions skill.
        e. Make the test changes. Keep edits minimal and on-convention.
        f. Run the test suite. The `YOUTUBE_API_KEY` secret should be
           available via the sandbox's secrets store; if it is not, tests
           that require it will skip — that is OK.
        g. Write a markdown report to `/tmp/qa-report.md` that includes:
           - Which scenario this was
           - The list of test files you added or modified (relative paths)
           - The pytest summary line
           - A short paragraph explaining what you changed and why

        ## What NOT to do

        - Do not modify files outside `{service_dir_rel}`.
        - Do not change the skill itself.
        - Do not introduce new top-level dependencies. If you think one is
           needed, write that in `/tmp/qa-report.md` instead of installing it.
        - Do not push to GitHub or open a PR. The conversation-starter
           handles reporting; you focus on the work.

        When you have written `/tmp/qa-report.md` and the test summary
        appears in your final response, your job is done.
        """
    )


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--scenario",
        required=True,
        help="Path to the scenario folder, e.g. scenarios/01_api_pr_update",
    )
    parser.add_argument(
        "--repo",
        default=os.environ.get("DEMO_REPO"),
        help="GitHub repo slug owner/name where this demo is hosted. "
        "Defaults to DEMO_REPO from .env.",
    )
    parser.add_argument(
        "--branch",
        default=os.environ.get("DEMO_BRANCH", "main"),
        help="Branch to clone in the sandbox. Defaults to DEMO_BRANCH or 'main'.",
    )
    parser.add_argument(
        "--title",
        default=None,
        help="Optional human-readable conversation title.",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Print the prompt that would be sent and exit. Does not call the API.",
    )
    args = parser.parse_args()

    scenario_dir = (REPO_ROOT / args.scenario).resolve()
    if not scenario_dir.is_dir():
        sys.exit(f"Scenario folder does not exist: {args.scenario}")

    prompt = _build_prompt(scenario_dir)

    if args.dry_run:
        print(prompt)
        return 0

    if not args.repo:
        sys.exit(
            "DEMO_REPO is not set. Either pass --repo owner/name or add "
            "DEMO_REPO to .env once you've pushed this repo to GitHub.",
        )

    title = args.title or f"API QA — {scenario_dir.name}"
    print(f"Starting conversation: {title}")
    print(f"  Repo:   {args.repo}@{args.branch}")
    print(f"  Prompt: {len(prompt)} chars")
    print()

    with OpenHandsClient() as client:
        start = client.start_conversation(
            initial_message=prompt,
            selected_repository=args.repo,
            selected_branch=args.branch,
            title=title,
        )
        app_id = start.get("app_conversation_id")
        if not app_id:
            task_id = start.get("id")
            if not task_id:
                sys.exit(f"Unexpected start-conversation response: {start}")
            print(f"Polling start-task {task_id} for conversation id…")
            task = client.poll_until_ready(task_id)
            app_id = task["app_conversation_id"]

        url = client.conversation_url(app_id)
        print(f"Conversation started: {url}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
