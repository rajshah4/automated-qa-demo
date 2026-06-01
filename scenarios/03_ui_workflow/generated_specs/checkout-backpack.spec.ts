/**
 * Happy-path spec: Checkout an in-stock item (Sauce Labs Backpack)
 *
 * Workflow source: scenarios/03_ui_workflow/workflow.md
 *
 * Selector strategy
 * -----------------
 * Priority follows the front-end-testing skill's query order:
 *   1. getByRole  2. getByLabel  3. getByPlaceholder  4. getByText
 * The site (saucedemo.com v1) has minimal ARIA markup on several elements.
 * Where no semantic query reaches a unique target we fall back to the site's
 * `data-test` attributes — each fallback is annotated with a comment.
 */

import { test, expect } from '@playwright/test';

const BASE_URL = 'https://www.saucedemo.com/';
const USERNAME  = 'standard_user';
const PASSWORD  = 'secret_sauce';

test.describe('Checkout — Sauce Labs Backpack (happy path)', () => {
  test('logged-in user can add Backpack to cart, checkout, and see confirmation', async ({ page }) => {
    // ── 1. Navigate ─────────────────────────────────────────────────────────
    await page.goto(BASE_URL);

    // ── 2. Log in ────────────────────────────────────────────────────────────
    // No <label> elements on the form; falling back to placeholder (priority 3).
    await page.getByPlaceholder('Username').fill(USERNAME);
    await page.getByPlaceholder('Password').fill(PASSWORD);
    // input[type=submit] carries the button role; accessible name = value attr.
    await page.getByRole('button', { name: /login/i }).click();
    await page.waitForURL('**/inventory.html');

    // ── 3. Add Sauce Labs Backpack to cart ───────────────────────────────────
    // Scope to the card that contains the product name so getByRole is unique.
    const backpackCard = page.locator('.inventory_item').filter({ hasText: 'Sauce Labs Backpack' });
    await backpackCard.getByRole('button', { name: /add to cart/i }).click();

    // ── 4. Cart badge must show "1" ──────────────────────────────────────────
    // .shopping_cart_badge has no role/label; data-test fallback via CSS class.
    await expect(page.locator('.shopping_cart_badge')).toHaveText('1');

    // ── 5. Open cart ─────────────────────────────────────────────────────────
    // The cart icon is an <a> with no aria-label; navigating by CSS class.
    await page.locator('.shopping_cart_link').click();
    await page.waitForURL('**/cart.html');

    // ── 6. Proceed to checkout ───────────────────────────────────────────────
    await page.getByRole('button', { name: /checkout/i }).click();
    await page.waitForURL('**/checkout-step-one.html');

    // ── 7. Fill shipping form ────────────────────────────────────────────────
    // Inputs expose data-test attributes; using getByPlaceholder (priority 3).
    await page.getByPlaceholder('First Name').fill('Jane');
    await page.getByPlaceholder('Last Name').fill('QA');
    await page.getByPlaceholder('Zip/Postal Code').fill('90210');

    // ── 8. Continue to overview ──────────────────────────────────────────────
    // input[type=submit] — button role, accessible name = value "Continue".
    await page.getByRole('button', { name: /continue/i }).click();
    await page.waitForURL('**/checkout-step-two.html');

    // ── 9. Confirm Backpack appears in the order summary ─────────────────────
    await expect(
      page.locator('.cart_item').filter({ hasText: 'Sauce Labs Backpack' })
    ).toBeVisible();

    // ── 10. Finish the order ─────────────────────────────────────────────────
    await page.getByRole('button', { name: /finish/i }).click();
    await page.waitForURL('**/checkout-complete.html');

    // ── 11. Confirm success page ──────────────────────────────────────────────
    await expect(page.getByText(/thank you for your order/i)).toBeVisible();
  });
});
