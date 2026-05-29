"""Conversation-starter for UI QA scenarios.

Runs OUTSIDE the OpenHands sandbox. Reads a natural-language workflow
description and POSTs a self-contained task prompt to /api/v1/app-conversations
on the OpenHands platform. The conversation drives a real browser via the
SDK's BrowserToolSet, records the session with rrweb, and emits a maintainable
Playwright spec following the front-end-testing skill's conventions.

Usage:
    python -m agents.ui_qa_agent --scenario scenarios/03_ui_workflow
"""

from __future__ import annotations

import argparse
import os
import sys
import textwrap
from pathlib import Path

try:
    from dotenv import load_dotenv

    load_dotenv()
except ImportError:
    pass

from agents._client import OpenHandsClient

REPO_ROOT = Path(__file__).resolve().parent.parent


def _read_text(path: Path) -> str:
    if not path.is_file():
        sys.exit(f"Expected file does not exist: {path.relative_to(REPO_ROOT)}")
    return path.read_text(encoding="utf-8")


def _build_prompt(scenario_dir: Path) -> str:
    """Construct a self-contained task prompt for the UI QA conversation."""
    scenario_rel = scenario_dir.relative_to(REPO_ROOT)
    workflow_path = scenario_dir / "workflow.md"
    workflow_rel = workflow_path.relative_to(REPO_ROOT)
    _read_text(workflow_path)  # validate it exists; the agent will read it fresh

    generated_specs_rel = scenario_rel / "generated_specs"
    recordings_rel = scenario_rel / "recordings"

    return textwrap.dedent(
        f"""\
        You are the UI QA agent for the automated-qa-demo repo.

        ## Your task

        Drive a real browser through the workflow described at
        `{workflow_rel}`, then emit a maintainable Playwright spec the QA
        team will keep.

        1. Read `AGENTS.md` at the repo root for general project guidance.
        2. Read **both** skills before touching any code:
           - `skills/webapp-testing/SKILL.md` — runtime pattern for driving
             the browser (reconnaissance-then-action). Use the bundled
             `scripts/with_server.py` helper if you need a local server,
             though for this scenario the SUT is public.
           - `skills/front-end-testing/SKILL.md` — the quality bar for the
             spec you emit. Accessibility-first queries, idempotency, no
             `getByTestId` unless nothing else works.
        3. Read the workflow at `{workflow_rel}`.

        ## What to do

        a. Drive the workflow live, using Playwright (sync API, headless
           Chromium). Wait for `networkidle` after each navigation. Use
           reconnaissance (screenshots, DOM inspection) to identify the
           right selectors before acting.

        b. Record the entire browser session as rrweb output. Place the
           recording artifact under `{recordings_rel}/`. Name it
           `checkout-backpack.rrweb.json` (or `.zip` if you bundle multiple
           events files). Also save a screenshot of the final
           confirmation page as `{recordings_rel}/checkout-backpack-final.png`.

        c. Emit a standalone Playwright spec at
           `{generated_specs_rel}/checkout-backpack.spec.ts`. The spec must:
           - Use TypeScript and the `@playwright/test` runner.
           - Be runnable on its own with `npx playwright test`.
           - Follow the front-end-testing skill's query priority.
           - Be **idempotent** — no shared state between runs.
           - Include a brief header comment that links back to
             `{workflow_rel}` so future maintainers know the source of truth.

        d. Re-run the generated spec from scratch with
           `npx playwright test {generated_specs_rel}/checkout-backpack.spec.ts`
           to confirm it passes outside of your live driving.

        e. If you have time after the happy path passes, add one extra spec
           covering an edge case from the workflow's "Edge cases" section
           (e.g. the `locked_out_user` failure mode). Pick the most
           informative one. Keep this spec in the same folder.

        f. Write a markdown report to `/tmp/qa-report.md` containing:
           - The scenario name
           - The generated spec file paths (relative to the repo)
           - The recording file path
           - The Playwright run summary
           - A short paragraph explaining design decisions (why these
             selectors, which edge case you chose and why)

        ## What NOT to do

        - Do not modify files outside `{scenario_rel}`.
        - Do not change the skills.
        - Do not add a CI workflow file; the demo wires that up separately.
        - Do not introduce visual regression assertions.

        When `/tmp/qa-report.md` is written and the Playwright run summary
        appears in your final response, you are done.
        """
    )


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--scenario",
        default="scenarios/03_ui_workflow",
        help="Path to the scenario folder. Defaults to scenarios/03_ui_workflow.",
    )
    parser.add_argument(
        "--repo",
        default=os.environ.get("DEMO_REPO"),
        help="GitHub repo slug owner/name. Defaults to DEMO_REPO from .env.",
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

    title = args.title or f"UI QA — {scenario_dir.name}"
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
