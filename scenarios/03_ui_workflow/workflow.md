# UI Workflow Under Test: SauceDemo Checkout

This is the natural-language workflow description the UI QA agent reads.
It is intentionally written the way a product manager or QA lead would write
a ticket — not a Playwright spec. The agent's job is to turn this into a
maintainable, idempotent spec following the
[`front-end-testing`](../../skills/front-end-testing/SKILL.md) skill's
conventions.

## System under test

- **URL**: `https://www.saucedemo.com/v1/`
- **Auth**: standard test login (publicly documented on the site)
  - Username: `standard_user`
  - Password: `secret_sauce`
- **Why this site**: it's a public, stable, intentionally-built demo
  storefront with a known-good happy path and known-broken edge cases
  (deliberately problematic users for QA practice). It's representative of
  a real e-commerce checkout flow.

## Workflow: "Checkout an in-stock item"

**Acceptance criteria** (from the imaginary product team):

1. A logged-in user can add the **Sauce Labs Backpack** to their cart.
2. They can proceed to checkout and provide shipping info.
3. They see an order-confirmation page that includes the words
   "THANK YOU FOR YOUR ORDER" (or equivalent on the v1 site).

## Step-by-step user actions

1. Navigate to `https://www.saucedemo.com/v1/`.
2. Log in with `standard_user` / `secret_sauce`.
3. On the products page, click **Add to cart** on the **Sauce Labs Backpack** card.
4. Confirm the cart badge in the header shows `1`.
5. Click the cart icon to open the cart.
6. Click **Checkout**.
7. Fill in the checkout form:
   - First name: any non-empty string
   - Last name: any non-empty string
   - Postal code: any non-empty string
8. Click **Continue**.
9. On the overview page, confirm the **Sauce Labs Backpack** appears in
   the item list.
10. Click **Finish**.
11. Confirm the success page is shown with a thank-you message.

## What the generated spec must do

- Live at `generated_specs/checkout-backpack.spec.ts` (Playwright + TypeScript).
- Be **idempotent** per the front-end-testing skill's rules: no shared state
  between runs, no reliance on the order of test execution.
- Query elements **by role / accessible name first** (`getByRole`,
  `getByLabel`, `getByText`). Only fall back to `getByTestId` (the site
  exposes `data-test` attributes) when no semantic query works — and document
  why in a comment when this happens.
- Record the browser session via rrweb so the PR comment can embed it.
- Take a screenshot of the final confirmation page as evidence.

## Edge cases the agent should also consider

Once the happy path is green, add at least one additional spec covering one
of these (the agent picks the most informative one):

- The **`locked_out_user`** account (`locked_out_user` / `secret_sauce`) —
  login should fail with a visible error.
- The **`problem_user`** account — images on the products page render
  incorrectly. A spec that asserts every product card has a non-broken
  image is a good catch.
- The **`performance_glitch_user`** account — pages load slowly. A spec
  with a tight timeout that documents the expectation.
- **Sort by Price (low → high)** — on the inventory page there is a sort
  dropdown (`product_sort_container`). Selecting "Price (low to high)"
  must re-order the visible product cards by ascending price. A spec
  should read the price text from each `.inventory_item_price` element
  after sorting and assert the list is non-decreasing.

## Out of scope

- Visual regression testing.
- Mobile viewports (the v1 site doesn't reliably support them).
- The "Reset App State" hamburger menu — not part of the user workflow.
