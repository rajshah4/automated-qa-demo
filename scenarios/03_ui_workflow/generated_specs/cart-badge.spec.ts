/**
 * Edge-case spec: Cart badge increments / decrements on the inventory page
 *
 * Workflow source: scenarios/03_ui_workflow/workflow.md
 *   "Cart badge increments after adding an item" section (added in PR #16)
 *
 * Why this edge case?
 *   The cart badge is the only visible cart-state signal on the inventory page.
 *   If someone refactors the cart store (e.g., switches from React state to a
 *   global store, or introduces a caching layer), the badge is likely to silently
 *   regress — it can show a stale count or disappear entirely.  This spec pins
 *   the increment / decrement contract so that regression surfaces immediately.
 *
 * What this spec verifies:
 *   1. No badge is rendered when the cart is empty.
 *   2. Adding one product makes the badge appear showing "1".
 *   3. Adding a second distinct product increments the badge to "2".
 *   4. Removing the first product decrements the badge to "1".
 *   5. Removing the last product removes the badge element entirely
 *      (the site only renders the badge when count > 0).
 *
 * Query strategy:
 *   - getByRole for the "Add to cart" and "Remove" buttons, scoped to each
 *     product card using page.locator() to avoid ambiguity between cards.
 *   - data-test attributes used where the site provides no semantic handle
 *     (the cart badge span has data-test="shopping-cart-badge"; a <span> has
 *     no implicit ARIA role that Playwright can address by name).
 *
 * Idempotency: each test navigates to the inventory page fresh (no shared
 * cart state between tests).
 */

import { test, expect } from '@playwright/test';

const BASE_URL = 'https://www.saucedemo.com/v1/';

async function loginAsStandardUser(page: Parameters<Parameters<typeof test>[1]>[0]['page']) {
  await page.goto(BASE_URL);
  await page.waitForLoadState('networkidle');
  await page.getByPlaceholder('Username').fill('standard_user');
  await page.getByPlaceholder('Password').fill('secret_sauce');
  // Login button is <input type="submit"> — no inner text; addressed by data-test.
  await page.locator('[data-test="login-button"]').click();
  await page.waitForLoadState('networkidle');
}

test.describe('Cart badge – increment / decrement on inventory page', () => {

  test('badge is absent when the cart is empty', async ({ page }) => {
    await loginAsStandardUser(page);
    await expect(page).toHaveURL(/inventory/);

    // The badge span is only rendered when count > 0
    await expect(page.locator('.shopping_cart_badge')).toHaveCount(0);
  });

  test('badge appears as "1" after adding one product', async ({ page }) => {
    await loginAsStandardUser(page);

    await page.locator('[data-test="add-to-cart-sauce-labs-backpack"]').click();

    // Badge must appear immediately (synchronous state update)
    const badge = page.locator('[data-test="shopping-cart-badge"]');
    await expect(badge).toBeVisible();
    await expect(badge).toHaveText('1');
  });

  test('badge increments to "2" after adding a second distinct product', async ({ page }) => {
    await loginAsStandardUser(page);

    await page.locator('[data-test="add-to-cart-sauce-labs-backpack"]').click();
    await expect(page.locator('[data-test="shopping-cart-badge"]')).toHaveText('1');

    await page.locator('[data-test="add-to-cart-sauce-labs-bike-light"]').click();
    await expect(page.locator('[data-test="shopping-cart-badge"]')).toHaveText('2');
  });

  test('badge decrements after removing a product and disappears when cart is empty', async ({ page }) => {
    await loginAsStandardUser(page);

    // Build a cart with two items
    await page.locator('[data-test="add-to-cart-sauce-labs-backpack"]').click();
    await page.locator('[data-test="add-to-cart-sauce-labs-bike-light"]').click();
    await expect(page.locator('[data-test="shopping-cart-badge"]')).toHaveText('2');

    // Remove first item → badge decrements to 1
    // The "Add to cart" button becomes "Remove" after being clicked;
    // data-test mirrors the product slug.
    await page.locator('[data-test="remove-sauce-labs-backpack"]').click();
    await expect(page.locator('[data-test="shopping-cart-badge"]')).toHaveText('1');

    // Remove last item → badge element must disappear entirely
    await page.locator('[data-test="remove-sauce-labs-bike-light"]').click();
    await expect(page.locator('[data-test="shopping-cart-badge"]')).toHaveCount(0);
  });

});
