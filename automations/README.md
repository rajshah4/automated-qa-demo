# OpenHands Automation — PR QA Trigger

This directory documents the OpenHands Automation that runs the QA workflow
whenever a pull request is opened on `rajshah4/automated-qa-demo`.

It is the **production-target architecture** for the demo — the same mechanism
a customer would deploy. The GitHub Actions workflow (`qa.yml`) remains as a
reference and fallback; both pipelines fire on the same PR.

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

1. **Detects which scenario the PR touches** — same heuristic as `qa.yml`'s
   "Decide scenario" step: reads the PR's changed-file list via `gh pr view`,
   then picks the most-affected `scenarios/<N>_<name>/` folder.

2. **Checks out the PR branch** — so the QA work runs against the actual
   in-flight change, not main.

3. **Reads `AGENTS.md` and the relevant skill** — the skill is the source of
   truth for how tests are written. No hardcoded logic in the automation prompt.

4. **Runs the QA work** — follows the exact same task specification as
   `agents/api_qa_agent.py` (`_build_prompt`) or `agents/ui_qa_agent.py`
   (`_build_prompt`), depending on the detected scenario.

5. **Posts a PR comment** — the comment is clearly marked as coming from the
   OpenHands Automation so it is visually distinct from the Actions comment:

   ```
   🤖 Automated QA (via OpenHands Automation) — `<scenario>`
   ```

   The Actions comment begins with `✅ Automated QA —`. Both appear on the
   same PR. That's the demo: the customer sees two independent QA triggers
   producing the same result.

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

## Comparison with the GitHub Actions path

| | OpenHands Automation | GitHub Actions (`qa.yml`) |
|---|---|---|
| **Trigger** | `pull_request.opened` webhook via automation service | `pull_request` workflow event |
| **QA work runs in** | OpenHands conversation sandbox | OpenHands conversation sandbox |
| **Scenario detection** | Agent reads `gh pr view` output | Shell script using `gh pr view` |
| **PR comment header** | 🤖 **Automated QA (via OpenHands Automation)** | ✅ **Automated QA —** |
| **GIF preview (UI)** | Not included (text-only comment) | Committed to PR branch |
| **Artifact bundle** | Not uploaded | Actions artifact (30-day retention) |
| **Config to maintain** | Automation prompt in the service | `qa.yml` YAML |

The Automation path omits the GIF and artifact bundle for simplicity — that's
an intentional scope choice for the demo. The customer can see the QA summary
and conversation link from the Automation comment; the full videos and reports
are on the Actions side.

---

## Re-registering the automation

If the automation needs to be recreated, run:

```bash
source .env
python3 /tmp/make_payload.py  # regenerates /tmp/automation-payload.json
curl -s -X POST "https://app.all-hands.dev/api/automation/v1/preset/prompt" \
  -H "Authorization: Bearer $OPENHANDS_API_KEY" \
  -H "Content-Type: application/json" \
  --data-binary @/tmp/automation-payload.json | python3 -m json.tool
```

The prompt source is in `agents/api_qa_agent.py` and `agents/ui_qa_agent.py`
(`_build_prompt` functions). The automation prompt is a meta-prompt that reads
those functions at run time to get the current task specification, so updating
the agent scripts automatically updates the QA work without re-registering.

---

## Secrets required in the sandbox

| Secret name | Used for |
|---|---|
| `GITHUB_TOKEN` | `gh pr view` (read PR files), `gh pr comment` (post comment) |
| `YOUTUBE_API_KEY` | Running the API test suites (scenarios 01 and 02) |
