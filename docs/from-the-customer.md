# Design questions from customer feedback

Open questions surfaced while showing this demo. Each has a provisional
answer and a pointer to where it would land in the codebase. These are
deliberately *unresolved* — they're the conversation we want to have, not
foregone conclusions.

---

## 1. "We already have tests. How does this not throw them away?"

**The concern.** In a real codebase, QA already exists — unit tests,
integration tests, fixtures, helper modules. An agent that generates fresh
test files from scratch every time is worse than useless: it creates noise,
duplicates coverage, and disrespects the patterns the team already follows.

**Provisional answer — make the skill brownfield-aware.**

The `api-qa-conventions` skill should require the agent to do a
**reconnaissance pass before any write**:

1. Scan for existing test files that touch the same endpoint(s).
2. If found, **extend** them. Match the existing pytest style
   (class-based vs. function-based), fixture names, parametrization
   shape, mocking strategy.
3. Only write a new file when no existing one is logically responsible.
4. In the report, cite the file the agent followed (`"Extended
   test_search.py to cover region/maxResults; matched existing parametrize
   shape"`).

**Where it lands.** New section in
[`skills/api-qa-conventions/SKILL.md`](../skills/api-qa-conventions/SKILL.md)
called "Brownfield first: extend before you create."

**Why this is a skill change, not agent code.** The agent doesn't need new
tools to do this — it already has a file reader. What's missing is the
*instruction* to look first. That's the skill's job.

---

## 2. "Should the generated tests be saved?"

**The concern.** If the agent generates a test for PR #42, runs it, and
the run vanishes, the team gets no asset. The next PR re-derives the same
test. The team is paying the agent to do the same work repeatedly while
their coverage stays flat.

**Provisional answer — yes, tests are first-class artifacts. Commit them.**

The agent's output is not "a comment on a PR." It's a **commit to the PR
branch** that adds or updates the test files, plus a comment that links to
those files. Specifically:

- New or modified test files land in the repo's normal test directories
  (`service/tests/` in our case), in the same commit shape a human would
  produce.
- The PR comment links to the diff of that commit (`"Added 3 tests in
  test_search.py — see commit abc123"`).
- The agent never opens its own PR. It pushes to the existing PR's branch
  using the existing PR author's GitHub identity (via the sandbox's GH
  token), so the author keeps ownership.
- A bot-account variant exists for teams that prefer separation (config flag).

**Where it lands.** [`reporters/`](../reporters/) — the reporter is more
than a comment writer; it's a "commit + comment" step. The Phase 9 design
needs to reflect this.

**Side effect.** Over months, the team's test coverage genuinely grows
from agent runs. That's the "compounding QA" story we should tell — every
PR makes the suite stronger, not just the PR.

---

## 3. "When we discover a new edge case, how does the agent learn it forever?"

**The concern.** The agent catches a quota-exhausted error on the YouTube
API today. Tomorrow, a different engineer files a PR for a different
endpoint — does the agent remember to test quota exhaustion there too?
Without a feedback loop, every team relearns every edge case.

**Provisional answer — skills are living documents. Treat them as code.**

Two-part loop:

**Part A — the agent emits "skill update candidates" at the end of every run.**

The report should include a section like:

```markdown
## Skill update candidates

While running this scenario I encountered a failure mode that isn't in
api-qa-conventions yet:

- Upstream returned 503 with a Retry-After header. The skill's error-path
  table covers 5xx → 502, but doesn't mention Retry-After propagation.

Suggested addition (proposed text): ...
```

This costs nothing per run and surfaces patterns naturally.

**Part B — a separate "skill curator" loop (not in this phase).**

A different agent (or a human) batches these candidates weekly and opens
PRs to update the skill files themselves. Skills get versioned, reviewed,
merged like any other code. The customer's QA lead is in the loop.

**Where it lands.** Part A is a one-paragraph addition to both
`api-qa-conventions/SKILL.md` and the automation prompt in
[`automations/build_prompt.py`](../automations/build_prompt.py). Part B is a future
phase.

**Why this matters for the pitch.** This is the "model-agnostic" story
made concrete in a different dimension: not just *which LLM* you use, but
*which test conventions* you've codified. The skills are the customer's IP.

---

## 4. "What happens when a test fails — does the agent try to fix it?"

**The concern.** Two very different failure modes, conflated:

| Failure mode | Right answer |
|---|---|
| The test is broken (stale selector, brittle assertion, dep moved) | Agent should fix the test |
| The code is broken (real regression, the test caught a bug) | Agent should **not** fix the code |
| Ambiguous (which is wrong?) | Agent should diagnose and ask |

**Provisional answer — explicit triage, with a policy knob.**

After a failing run, the agent goes through a triage step:

1. **Is the test outdated relative to current behavior?** (e.g. the API now
   returns `videoId` instead of `id`.) → Update the test. Cite the change.
2. **Is the test brittle/flaky?** (timing, ordering, env-dependent.) →
   Reshape the test to be robust. Cite the failure.
3. **Is the assertion right and the code wrong?** → Stop. Report the bug.
   Do not touch the code. The PR author owns the fix.
4. **Cannot tell?** → Report findings, propose two hypotheses, ask the
   human in the PR comment.

The default policy is **fix tests, never fix application code**. A config
flag (`AGENT_MAY_PATCH_APP_CODE=true`) exists for teams that want a more
aggressive auto-fix loop — opt-in only.

**Where it lands.** New section in `api-qa-conventions/SKILL.md` called
"What to do when a test fails." Also referenced in the prompts the agents
build. The policy flag would be a Phase 8 (LLM profiles) or Phase 10
(docs / security) concern.

**Why this distinction matters.** A QA tool that "helpfully fixes" your
production code is a liability. A QA tool that fixes the test scaffolding
and flags real bugs is a force multiplier. The customer needs to see we
understand which is which.

---

## Implementation checklist

These are tracked in the project task list. None are blockers for the
walkthrough — they're the "Phase 2 of the demo, once you've signed."

- [ ] **Skill: brownfield-first reconnaissance** → `api-qa-conventions`
- [ ] **Reporter: commit tests to PR branch** → `reporters/`
- [ ] **Skill update candidates section** → both skills + agent prompts
- [ ] **Failure triage policy** → `api-qa-conventions` + agent prompts
- [ ] **Policy flag plumbing** → `llm-profiles/` (or wherever config lives)
- [ ] **Skill curator loop** → future, separate agent
