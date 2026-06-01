/**
 * Happy-path spec: Checkout the Sauce Labs Backpack
 *
 * Workflow source: scenarios/03_ui_workflow/workflow.md
 *
 * Covers the full purchase journey for a logged-in standard_user:
 *   Login → Add Backpack to cart → Cart → Checkout form → Overview → Finish → Confirmation
 *
 * Query strategy (front-end-testing skill priority):
 *   1. getByRole  – for buttons and links identified by their accessible name
 *   2. getByLabel – for labelled form fields (falls back to getByPlaceholder
 *      when the site omits <label> elements in favour of placeholder text)
 *   3. getByText  – for visible headings / confirmation copy
 *   4. data-test  – only when no semantic query is unambiguous; documented inline
 */

import { test, expect } from '@playwright/test';

const BASE_URL = 'https://www.saucedemo.com/v1/';
const USERNAME = 'standard_user';
const PASSWORD = 'secret_sauce';

/**
 * Log in to SauceDemo and land on the inventory page.
 * Extracted as a helper to keep each test self-contained (idempotency).
 */
async function login(page: Parameters<Parameters<typeof test>[1]>[0]['page']) {
  await page.goto(BASE_URL);
  await page.waitForLoadState('networkidle');
  // The login form uses placeholder text instead of <label> elements, so
  // getByPlaceholder is the highest-fidelity accessible query available here.
  await page.getByPlaceholder('Username').fill(USERNAME);
  await page.getByPlaceholder('Password').fill(PASSWORD);
  // The login button is <input type="submit" data-test="login-button">.
  // Input submit elements have no inner text; data-test is the best handle.
  await page.locator('[data-test="login-button"]').click();
  await page.waitForLoadState('networkidle');
}

test.describe('Checkout – Sauce Labs Backpack (happy path)', () => {
  test('standard_user can add the Backpack, checkout, and see the confirmation', async ({ page }) => {
    await login(page);

    // ── Step 1: Products page ─────────────────────────────────────────────────
    await expect(page).toHaveURL(/inventory/);

    // The inventory page has six "Add to cart" buttons, one per product.
    // Using data-test to scope to the exact product card because getByRole('button',
    // { name: /add to cart/i }) would match all six and .first() would be brittle
    // if the server-side sort order ever changes.
    const addBackpackBtn = page.locator('[data-test="add-to-cart-sauce-labs-backpack"]');
    await addBackpackBtn.click();

    // Cart badge must appear showing "1"
    await expect(page.locator('.shopping_cart_badge')).toHaveText('1');

    // ── Step 2: Cart page ─────────────────────────────────────────────────────
    // The cart icon is an <a> element; navigate by clicking it.
    await page.locator('.shopping_cart_link').click();
    await page.waitForLoadState('networkidle');
    await expect(page).toHaveURL(/cart/);

    // Backpack must be in the cart
    await expect(page.getByText('Sauce Labs Backpack')).toBeVisible();

    // ── Step 3: Checkout form ─────────────────────────────────────────────────
    await page.getByRole('button', { name: /checkout/i }).click();
    await page.waitForLoadState('networkidle');
    await expect(page).toHaveURL(/checkout-step-one/);

    await page.getByPlaceholder('First Name').fill('Jane');
    await page.getByPlaceholder('Last Name').fill('Smith');
    await page.getByPlaceholder('Zip/Postal Code').fill('12345');
    await page.getByRole('button', { name: /continue/i }).click();
    await page.waitForLoadState('networkidle');

    // ── Step 4: Overview page ─────────────────────────────────────────────────
    await expect(page).toHaveURL(/checkout-step-two/);
    await expect(page.getByText('Sauce Labs Backpack')).toBeVisible();

    await page.getByRole('button', { name: /finish/i }).click();
    await page.waitForLoadState('networkidle');

    // ── Step 5: Confirmation page ─────────────────────────────────────────────
    await expect(page).toHaveURL(/checkout-complete/);
    // The v1 site renders the confirmation heading in a <h2 data-test="complete-header">
    await expect(page.getByText(/thank you for your order/i)).toBeVisible();
  });
});
