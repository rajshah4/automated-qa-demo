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

    # override=True so .env wins over stale shell env vars.
    load_dotenv(override=True)
except ImportError:
    pass

from agents._client import OpenHandsClient
from agents._ci import emit as ci_emit
from agents.runs import log_run

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
    config_rel = scenario_rel / "playwright.config.ts"
    report_rel = scenario_rel / "playwright-report"
    results_rel = scenario_rel / "test-results"

    return textwrap.dedent(
        f"""\
        You are the UI QA agent for the automated-qa-demo repo.

        ## Your task

        Drive a real browser through the workflow described at
        `{workflow_rel}`, emit a maintainable Playwright spec the QA team
        will keep, and produce the rich artifacts a QA lead expects: HTML
        report, trace files (for time-travel debugging), per-test videos,
        and on-failure screenshots.

        1. Read `AGENTS.md` at the repo root for general project guidance.
        2. Read **both** skills before touching any code:
           - `skills/webapp-testing/SKILL.md` — runtime pattern for driving
             the browser (reconnaissance-then-action).
           - `skills/front-end-testing/SKILL.md` — the quality bar for the
             spec you emit. Accessibility-first queries, idempotency, no
             `getByTestId` unless nothing else works.
        3. Read the workflow at `{workflow_rel}`.

        ## What to do

        a. **Playwright config.** Create `{config_rel}` with these settings
           so the run produces canonical QA artifacts. Use
           `@playwright/test`'s `defineConfig`:

           ```ts
           import {{ defineConfig, devices }} from '@playwright/test';
           export default defineConfig({{
             testDir: './generated_specs',
             fullyParallel: true,
             reporter: [
               ['list'],
               ['html', {{ outputFolder: 'playwright-report', open: 'never' }}],
             ],
             use: {{
               trace: 'on',                 // time-travel debugging for every test
               video: 'on',                 // per-test video
               screenshot: 'only-on-failure',
               actionTimeout: 15_000,
             }},
             projects: [
               {{ name: 'chromium', use: {{ ...devices['Desktop Chrome'] }} }},
             ],
           }});
           ```

           The agent that runs the tests must use this config. Run with:
           `cd {scenario_rel} && npx playwright test`

        b. **Drive the workflow live first** (sync Playwright API or the
           browser tool) to do reconnaissance. Wait for `networkidle` after
           each navigation. Identify the right selectors before writing
           assertions.

        c. **Emit a standalone happy-path spec** at
           `{generated_specs_rel}/checkout-backpack.spec.ts`:
           - TypeScript + `@playwright/test`.
           - Follows the front-end-testing skill's query priority.
           - Idempotent (no shared state between tests).
           - Header comment links back to `{workflow_rel}`.

        d. **Add one edge-case spec** in the same folder covering an entry
           from the workflow's "Edge cases" section. Pick the most
           informative one and explain the choice in the spec's header
           comment and in the report.

        e. **Run the suite** via `cd {scenario_rel} && npx playwright test`.
           This will populate `{report_rel}/` (HTML report) and
           `{results_rel}/` (per-test traces, videos, screenshots) — these
           are the primary artifacts the QA team will look at.

        f. **(Optional, only if time allows)** Capture an rrweb session for
           the happy path at `{recordings_rel}/checkout-backpack.rrweb.json`
           and a final screenshot at
           `{recordings_rel}/checkout-backpack-final.png`. These are
           supplementary (stakeholder-friendly replay); the Playwright
           report and traces are the canonical engineering artifacts and
           must be present even if you skip rrweb.

        g. **Write the report** to `/tmp/qa-report.md` containing:
           - The scenario name.
           - The generated spec file paths.
           - **Where to find the rich artifacts** — explicitly mention
             `{report_rel}/index.html` and how to open trace files with
             `npx playwright show-trace {results_rel}/<test>/trace.zip` (or
             via `https://trace.playwright.dev/`).
           - The Playwright run summary (pass/fail counts, duration).
           - Short paragraph on design decisions (selector strategy, why
             you picked the edge case you did).

        ## What NOT to do

        - Do not modify files outside `{scenario_rel}`.
        - Do not change the skills.
        - Do not add a CI workflow file; the demo wires that up separately.
        - Do not introduce visual regression assertions.

        When `/tmp/qa-report.md` is written, `{report_rel}/index.html`
        exists, and the Playwright run summary appears in your final
        response, you are done.
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
    parser.add_argument(
        "--wait",
        action="store_true",
        help="Block until the conversation finishes and print final timing + cost.",
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
        ci_emit("conversation_id", app_id)
        ci_emit("conversation_url", url)

        scenario_rel = str(scenario_dir.relative_to(REPO_ROOT))
        log_run(app_id, scenario=scenario_rel, wait=False, client=client)

        if args.wait:
            print("Waiting for conversation to finish…")
            row = log_run(app_id, scenario=scenario_rel, wait=True, client=client)
            duration = row.get("duration_seconds") or 0
            print(
                f"Done: status={row.get('execution_status')} "
                f"duration={int(duration // 60)}m{int(duration % 60):02d}s "
                f"cost=${row.get('cost_usd') or 0:.4f}"
            )
            ci_emit("execution_status", row.get("execution_status") or "")
            ci_emit("duration_seconds", str(int(duration)))
            ci_emit("cost_usd", f"{row.get('cost_usd') or 0:.4f}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
