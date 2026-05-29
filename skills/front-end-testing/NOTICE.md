# front-end-testing — Provenance

Vendored from **[citypaul/.dotfiles](https://github.com/citypaul/.dotfiles/blob/main/claude/.claude/skills/front-end-testing/SKILL.md)** at the `main` branch.

- Source: <https://github.com/citypaul/.dotfiles/blob/main/claude/.claude/skills/front-end-testing/SKILL.md>
- Last vendored: see git log for this file

## Why this is here

This skill is the **quality bar for the Playwright specs the UI QA agent emits**.
It encodes behavior-driven testing principles:

- Accessibility-first query priority (`getByRole` > `getByLabelText` > … > `getByTestId`)
- `expect.element()` with auto-retry instead of brittle waits
- Test idempotency rules (each test fully self-contained)
- MSW for network mocking instead of `fetch` patches
- The full anti-pattern catalog (`getByTestId` cargo culting, multi-assert `waitFor`, etc.)

It is loaded by [`agents/ui_qa_agent.py`](../../agents/ui_qa_agent.py).

## How to update

```bash
curl -fsSL "https://raw.githubusercontent.com/citypaul/.dotfiles/main/claude/.claude/skills/front-end-testing/SKILL.md" \
  -o skills/front-end-testing/SKILL.md
```
