/**
 * Checkout Happy-Path: Sauce Labs Backpack
 *
 * Source of truth: scenarios/03_ui_workflow/workflow.md
 * System under test: https://www.saucedemo.com/v1/
 *
 * Selector strategy (per front-end-testing skill):
 *   1. getByRole (with accessible name) — preferred
 *   2. getByPlaceholder — for inputs that lack associated <label> elements
 *      (SauceDemo uses placeholder-only fields with no visible labels)
 *   3. getByText — for visible text nodes
 *   4. locator('[data-test="..."]') — last resort; used for the cart icon link
 *      because it is a label-less icon <a> with no accessible name.
 *      A comment marks every such fallback.
 *
 * Idempotency: @playwright/test creates a fresh browser context per test, so
 * no cart state persists across runs. Tests do not share state with each other.
 */

import { test, expect } from '@playwright/test';

const BASE_URL = 'https://www.saucedemo.com/v1/';
const USERNAME = 'standard_user';
const PASSWORD = 'secret_sauce';

// ---------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------

/** Log in as the given user and land on the inventory page. */
async function login(page: any, username = USERNAME, password = PASSWORD) {
  await page.goto(BASE_URL, { waitUntil: 'networkidle' });

  // Inputs have no associated <label> elements; placeholder is the best
  // accessible handle available on this site.
  await page.getByPlaceholder('Username').fill(username);
  await page.getByPlaceholder('Password').fill(password);

  // input[type=submit] carries the implicit ARIA role "button".
  await page.getByRole('button', { name: 'Login' }).click();
  await page.waitForLoadState('networkidle');
}

// ---------------------------------------------------------------------------
// Happy-path test
// ---------------------------------------------------------------------------

test.describe('Checkout: Sauce Labs Backpack — happy path', () => {
  test('logged-in user can add the backpack to cart, checkout, and see the confirmation', async ({
    page,
  }) => {
    // ── Step 1-2: Navigate and log in ───────────────────────────────────────
    await login(page);

    await expect(page).toHaveURL(/inventory/);

    // ── Step 3: Add Sauce Labs Backpack to cart ──────────────────────────────
    // Scope to the specific product card so we don't accidentally click
    // "Add to cart" on the wrong item when multiple cards are on screen.
    const backpackCard = page
      .locator('.inventory_item')
      .filter({ hasText: 'Sauce Labs Backpack' });

    await backpackCard.getByRole('button', { name: /add to cart/i }).click();

    // ── Step 4: Verify cart badge shows 1 ───────────────────────────────────
    // The cart badge is a numeric counter with no semantic role; CSS is the
    // most stable selector available.
    await expect(page.locator('.shopping_cart_badge')).toHaveText('1');

    // ── Step 5: Open the cart ────────────────────────────────────────────────
    // The cart icon is an <a> with no visible text or aria-label; data-test
    // is the only reliable handle (icon-only link, no accessible name).
    // data-test="shopping-cart-link"
    await page.locator('[data-test="shopping-cart-link"]').click();
    await page.waitForLoadState('networkidle');
    await expect(page).toHaveURL(/cart/);

    // The backpack should appear in the cart
    await expect(page.getByText('Sauce Labs Backpack')).toBeVisible();

    // ── Step 6: Start checkout ──────────────────────────────────────────────
    await page.getByRole('button', { name: 'Checkout' }).click();
    await page.waitForLoadState('networkidle');
    await expect(page).toHaveURL(/checkout-step-one/);

    // ── Step 7: Fill in shipping information ────────────────────────────────
    // Inputs have no <label> elements; placeholders are used as identifiers.
    await page.getByPlaceholder('First Name').fill('Jane');
    await page.getByPlaceholder('Last Name').fill('Tester');
    await page.getByPlaceholder('Zip/Postal Code').fill('10001');

    await page.getByRole('button', { name: 'Continue' }).click();
    await page.waitForLoadState('networkidle');
    await expect(page).toHaveURL(/checkout-step-two/);

    // ── Step 8: Confirm overview shows the backpack ──────────────────────────
    await expect(page.getByText('Sauce Labs Backpack')).toBeVisible();

    // ── Step 9: Finish the order ─────────────────────────────────────────────
    await page.getByRole('button', { name: 'Finish' }).click();
    await page.waitForLoadState('networkidle');
    await expect(page).toHaveURL(/checkout-complete/);

    // ── Step 10: Confirm the thank-you page ──────────────────────────────────
    // The confirmation heading is an <h2>; query by heading role for resilience.
    await expect(
      page.getByRole('heading', { name: /thank you for your order/i })
    ).toBeVisible();
  });
});
