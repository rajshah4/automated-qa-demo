# OpenHands Automation — PR QA Trigger

This directory documents the OpenHands Automation that runs the QA workflow
whenever a PR on `rajshah4/automated-qa-demo` is labeled with `openhands-qa`.

It is the **primary demo architecture** — the mechanism a customer would deploy.
There is no separate CI workflow — the Automation is the only trigger.

---

## Registered automation

| Field | Value |
|---|---|
| **Name** | `automated-qa-demo — PR QA trigger` |
| **Automation ID** | `5d152cb1-bb58-4402-9839-063fd9e76fe5` |
| **Backend** | OpenHands Cloud — `https://app.all-hands.dev` |
| **Model profile** | `GPT` (`litellm_proxy/gpt-5.5`) |
| **Trigger** | `pull_request.labeled` on `rajshah4/automated-qa-demo` |
| **Filter** | `repository.full_name == 'rajshah4/automated-qa-demo' && contains(pull_request.labels[].name, 'openhands-qa')` |
| **How to trigger** | Apply the `openhands-qa` label to any PR — automation fires within ~2 seconds |
| **Repo cloned** | `https://github.com/rajshah4/automated-qa-demo` @ `main` |
| **Timeout** | 1800 s (30 min) |
| **Enabled** | ✅ yes |

---

## What it does when the label is applied

1. **Detects which scenario the PR touches** — reads the PR's changed-file list
   via `gh pr view` and matches to the most-affected `scenarios/<N>_<name>/`
   folder. Branch name is used as a tiebreaker only when file paths are
   ambiguous (e.g. scenario 02 shares the same service code as scenario 01).

2. **Checks out the PR branch** — so the QA work runs against the actual
   in-flight change, not main.

3. **Reads `AGENTS.md` and the relevant skill** — the skill is the source of
   truth for how tests are written. No hardcoded logic in the automation prompt.

4. **Runs the QA work** — follows the exact same task specification as
   `automations/build_prompt.py`, reading the task specification from the
   skills and the scenario folder, depending on the detected scenario.

5. **Commits artifacts back to the PR branch** — generated test files, Playwright
   specs, `playwright.config.ts`, and GIF previews (converted from `.webm`
   recordings via ffmpeg) are staged under `$SCENARIO/` and pushed with
   `[skip ci]` to avoid re-triggering workflows.

6. **Posts a PR comment** — includes an inline summary table, the full
   `qa-report.md` in a collapsible block, and each generated file's full
   contents in a collapsible block — everything readable without leaving the PR:

   ```
   🤖 Automated QA (via OpenHands Automation) — `<scenario>`
   ```

---

## How to verify the automation is registered

```bash
# Requires OPENHANDS_API_KEY from .env
source .env

# List all automations (should include this one in the results)
curl -s "https://app.all-hands.dev/api/automation/v1" \
  -H "Authorization: Bearer $OPENHANDS_API_KEY" | python3 -m json.tool

# Get this automation specifically
curl -s "https://app.all-hands.dev/api/automation/v1/5d152cb1-bb58-4402-9839-063fd9e76fe5" \
  -H "Authorization: Bearer $OPENHANDS_API_KEY" | python3 -m json.tool
```

Or view it in the OpenHands Cloud UI at `https://app.all-hands.dev` → Automations.

---

## How to trigger a manual test run

```bash
source .env

# Dispatch a run (no event payload — agent falls back to gh pr list)
curl -s -X POST \
  "https://app.all-hands.dev/api/automation/v1/5d152cb1-bb58-4402-9839-063fd9e76fe5/dispatch" \
  -H "Authorization: Bearer $OPENHANDS_API_KEY" \
  -H "Content-Type: application/json" | python3 -m json.tool

# Check run status
curl -s \
  "https://app.all-hands.dev/api/automation/v1/5d152cb1-bb58-4402-9839-063fd9e76fe5/runs" \
  -H "Authorization: Bearer $OPENHANDS_API_KEY" | python3 -m json.tool
```

When `status` moves from `PENDING` → `RUNNING` → `COMPLETED`, check the PR for
the 🤖 comment.

---

## Re-registering the automation

If the automation needs to be recreated from scratch, the prompt is maintained
in `automations/build_prompt.py`. Run:

```bash
source .env
python3 automations/build_prompt.py   # writes /tmp/automation-payload.json
curl -s -X POST "https://app.all-hands.dev/api/automation/v1/preset/prompt" \
  -H "Authorization: Bearer $OPENHANDS_API_KEY" \
  -H "Content-Type: application/json" \
  --data-binary @/tmp/automation-payload.json | python3 -m json.tool
```

To update the prompt on the existing automation without re-registering:

```bash
source .env
python3 automations/build_prompt.py
python3 -c "
import json
p = json.load(open('/tmp/automation-payload.json'))
open('/tmp/patch.json','w').write(json.dumps({'prompt': p['prompt']}))
"
curl -s -X PATCH \
  "https://app.all-hands.dev/api/automation/v1/5d152cb1-bb58-4402-9839-063fd9e76fe5" \
  -H "Authorization: Bearer $OPENHANDS_API_KEY" \
  -H "Content-Type: application/json" \
  --data-binary @/tmp/patch.json | python3 -m json.tool
```

The prompt in `automations/build_prompt.py` is the single source of truth
for what work the automation does. Edit it there and run the PATCH command above
to push the update live.

---

## Secrets required in the sandbox

| Secret name | Used for |
|---|---|
| `GITHUB_TOKEN` | `gh pr view` (read PR files), `gh pr comment` (post comment) |
| `YOUTUBE_API_KEY` | Running the API test suites (scenarios 01 and 02) |
