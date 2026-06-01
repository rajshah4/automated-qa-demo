# agents/

> **These scripts are used by the GitHub Actions workflow (`qa.yml`) only.**
> They are NOT used by the OpenHands Automation.
>
> The demo has two independent QA trigger paths:
>
> | Path | What starts the conversation |
> |---|---|
> | **OpenHands Automation** (primary demo) | The automation's own prompt in `automations/build_prompt.py` — runs entirely inside the sandbox, no external script needed |
> | **GitHub Actions** (reference implementation) | `qa.yml` calls `api_qa_agent.py` / `ui_qa_agent.py` from this folder on an Actions runner |
>
> If you're exploring the demo trigger architecture, start with
> [`automations/README.md`](../automations/README.md).
> This folder only matters if you're working on the Actions path or want
> to kick off a conversation manually from your laptop.

Conversation-starter scripts. They run **outside** the OpenHands sandbox
and POST a self-contained task prompt to the V1 Conversation API. The
conversation that gets started does the actual QA work inside its own
sandbox.

| Script | Purpose |
|---|---|
| `_client.py` | Tiny V1 API client (httpx). Reads `OPENHANDS_API_KEY` from env. |
| `api_qa_agent.py` | Starts a conversation for Scenarios 1 and 2 (API). |
| `ui_qa_agent.py` | Starts a conversation for Scenario 3 (UI). |
| `fetch_artifacts.py` | After a conversation finishes, pulls generated files out of the sandbox so Actions can commit them. |
| `runs.py` | Local `runs.jsonl` ledger — tracks conversation IDs, cost, and duration. |
| `_ci.py` | Helpers for writing to `$GITHUB_OUTPUT` so Actions can pass values between steps. |

## How they work

```
   Your machine                   OpenHands Cloud                Sandbox
   ┌─────────────────┐          ┌──────────────────┐          ┌──────────────────┐
   │ python -m       │  POST    │ /api/v1/         │  spins   │ Clones DEMO_REPO │
   │ agents.api_…    ├─────────►│ app-conversations├─────────►│ Auto-loads       │
   │                 │ Bearer   │                  │   up     │ AGENTS.md +      │
   │                 │ token    │                  │          │ skills/          │
   └─────────────────┘          └──────────────────┘          │ Does the QA work │
                                         │                    │ Writes report    │
                                         ▼                    └──────────────────┘
                                  Conversation URL
                                  printed to stdout
```

The agents do **not** ship code into the sandbox. They tell the sandbox what
to do; the sandbox already has the repo, the skills, and the tools.

## Quick start

```bash
# 1. Install the only client-side dependency
uv add httpx python-dotenv

# 2. Fill in .env (already done — OPENHANDS_API_KEY is set)
#    plus DEMO_REPO once you've pushed this repo to GitHub
$EDITOR .env

# 3. Dry-run to see exactly what prompt would be sent
python -m agents.api_qa_agent --scenario scenarios/01_api_pr_update --dry-run

# 4. Kick off the real conversation
python -m agents.api_qa_agent --scenario scenarios/01_api_pr_update
# → prints a conversation URL like:
#   https://app.all-hands.dev/conversations/<id>
```

## CLI flags

Both `api_qa_agent.py` and `ui_qa_agent.py` accept:

| Flag | Default | What it does |
|---|---|---|
| `--scenario PATH` | (required for api) | Scenario folder to invoke |
| `--repo OWNER/NAME` | `$DEMO_REPO` | GitHub repo for the sandbox to clone |
| `--branch NAME` | `$DEMO_BRANCH` or `main` | Branch to clone |
| `--title STR` | auto-generated | Human-readable conversation title |
| `--dry-run` | off | Print the prompt and exit (no API call) |

## What's NOT in here

- No agent classes, no tools, no skills. That all lives elsewhere:
  - Tools come from the OpenHands sandbox runtime (terminal, file editor,
    BrowserToolSet).
  - Skills live in `skills/` at the repo root and auto-load via `AGENTS.md`.
  - The "agent code" is the prompt these scripts build — that's the
    whole point.

- No PR-posting logic. The conversation itself can run `gh pr comment` if
  the sandbox has a GitHub token. That keeps the scripts here purely about
  *starting* work, not orchestrating it.
