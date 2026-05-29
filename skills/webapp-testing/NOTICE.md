# webapp-testing — Provenance

Vendored from **[anthropics/skills](https://github.com/anthropics/skills/tree/main/skills/webapp-testing)** at the `main` branch.

- Source: <https://github.com/anthropics/skills/tree/main/skills/webapp-testing>
- License: see `LICENSE.txt` (carried over from upstream, unchanged)
- Last vendored: see git log for this directory

## Why this is here

This skill encodes the **runtime pattern** the UI QA agent uses to drive a real
browser via Playwright: reconnaissance-then-action, `with_server.py` for server
lifecycle, headless Chromium, accessibility-first selectors.

It is loaded by [`agents/ui_qa_agent.py`](../../agents/ui_qa_agent.py).

## How to update

```bash
# From the repo root:
rm -rf skills/webapp-testing
git clone --depth=1 --filter=blob:none --sparse https://github.com/anthropics/skills.git /tmp/anthropic-skills
cd /tmp/anthropic-skills && git sparse-checkout set skills/webapp-testing
cp -R /tmp/anthropic-skills/skills/webapp-testing skills/
```

Re-add this `NOTICE.md` afterwards. Do not modify the upstream skill files;
if you need different behavior, layer a project-specific skill on top instead.
