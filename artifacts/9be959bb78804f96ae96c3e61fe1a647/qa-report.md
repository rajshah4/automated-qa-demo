# QA Report — Scenario 03: UI Workflow (SauceDemo Checkout)

**Date:** 2026-05-29  
**Agent:** UI QA Agent (OpenHands)  
**System under test:** https://www.saucedemo.com/v1/ (Sauce Labs demo storefront)

---

## Generated Spec Files

| File | Description |
|------|-------------|
| `scenarios/03_ui_workflow/generated_specs/checkout-backpack.spec.ts` | Happy-path: add Sauce Labs Backpack to cart, complete checkout, verify confirmation |
| `scenarios/03_ui_workflow/generated_specs/checkout-locked-out.spec.ts` | Edge case: `locked_out_user` login is rejected with a visible error message |

## Recording Artifacts

| File | Description |
|------|-------------|
| `scenarios/03_ui_workflow/recordings/checkout-backpack.rrweb.json` | rrweb DOM-snapshot recording of the live checkout session (99 events) |
| `scenarios/03_ui_workflow/recordings/checkout-backpack-final.png` | Screenshot of the order confirmation page (`/checkout-complete.html`) |

## Playwright Run Summary

```
Running 2 tests using 2 workers

  ✓  1 [chromium] › generated_specs/checkout-locked-out.spec.ts:28:7 › Authentication edge case: locked-out user › locked_out_user sees a clear error message and stays on the login page (1.3s)
  ✓  2 [chromium] › generated_specs/checkout-backpack.spec.ts:49:7 › Checkout: Sauce Labs Backpack — happy path › logged-in user can add the backpack to cart, checkout, and see the confirmation (1.6s)

  2 passed (2.4s)
```

---

## Design Decisions

### Selector strategy

SauceDemo's forms contain **no `<label>` elements** — every text field is identified only by a `placeholder` attribute. The spec therefore uses `getByPlaceholder()` for all form inputs rather than the higher-priority `getByLabel()`, and a comment in the spec explains why. Where semantic HTML gives a button an implicit `role="button"` (including `input[type=submit]`), `getByRole('button', { name: ... })` is used exclusively. The order-confirmation heading is queried via `getByRole('heading', { name: /thank you/i })` so the test is resilient to minor copy changes. The single CSS-class fallback — `.shopping_cart_badge` for the numeric cart counter — is necessary because the badge element has no accessible role or label; a comment marks this as intentional.

The cart icon link (`<a>` with no visible text and no `aria-label`) required a `data-test` fallback (`[data-test="shopping-cart-link"]`), also documented with a comment. This is the only `data-test` selector in the happy-path spec.

### Idempotency

`@playwright/test` creates a fresh browser context for every test by default, so the cart is always empty at test start and no side effects bleed between runs. Credentials are inlined constants; no external fixtures or databases are touched.

### Edge-case choice: `locked_out_user`

The `locked_out_user` scenario was chosen over `problem_user` or `performance_glitch_user` because:
1. It produces a **deterministic, text-based signal** ("Epic sadface: Sorry, this user has been locked out.") rather than a visual or timing assertion.
2. It covers the authentication error path that the happy-path spec deliberately avoids.
3. The assertion is straightforward with `getByText(/sorry, this user has been locked out/i)` — no fragile timeouts or pixel comparisons required.

### rrweb recording approach

The public saucedemo.com site's Content Security Policy blocks external `<script>` tag injection. The recording was produced by executing the rrweb bundle via Playwright's CDP `Runtime.evaluate` call after each page load, which bypasses CSP. Events are collected from `window.__rrweb_events` before each page navigation and concatenated into a single 99-event JSON file covering the full login → add-to-cart → checkout → confirmation flow.
