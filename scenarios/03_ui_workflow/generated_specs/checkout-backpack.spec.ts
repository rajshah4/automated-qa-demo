import { test, expect } from '@playwright/test';

// SauceDemo v1 redirects to https://www.saucedemo.com — the /v1 path is optional.
const BASE_URL = 'https://www.saucedemo.com';
const STANDARD_USER = 'standard_user';
const PASSWORD = 'secret_sauce';
const LOCKED_USER = 'locked_out_user';

async function login(page: any, username: string, password: string) {
  await page.goto(`${BASE_URL}/`);
  await page.waitForLoadState('networkidle');
  await page.getByPlaceholder('Username').fill(username);
  await page.getByPlaceholder('Password').fill(password);
  await page.getByRole('button', { name: 'LOGIN' }).click();
}

// ─── Happy path ───────────────────────────────────────────────────────────────

test.describe('Happy path: Checkout an in-stock item', () => {
  test('should allow a logged-in user to buy the Sauce Labs Backpack', async ({ page }) => {
    await login(page, STANDARD_USER, PASSWORD);

    // Verify we landed on the products page
    await expect(page).toHaveURL(/inventory/);

    // Add Sauce Labs Backpack to cart.
    // Multiple "Add to cart" buttons exist, so we use the data-test attribute
    // for unambiguous targeting.
    await page.locator('[data-test="add-to-cart-sauce-labs-backpack"]').click();

    // Cart badge should show 1
    const badge = page.locator('.shopping_cart_badge');
    await expect(badge).toHaveText('1');

    // Navigate to the cart
    await page.locator('.shopping_cart_link').click();
    await expect(page).toHaveURL(/cart/);

    // The Backpack should appear in the cart
    await expect(page.getByText('Sauce Labs Backpack')).toBeVisible();

    // Proceed to checkout — the site renders this as a <button> (data-test="checkout")
    await page.locator('[data-test="checkout"]').click();
    await expect(page).toHaveURL(/checkout-step-one/);

    // Fill shipping info using the data-test attributes exposed by the site
    await page.locator('[data-test="firstName"]').fill('Jane');
    await page.locator('[data-test="lastName"]').fill('Doe');
    await page.locator('[data-test="postalCode"]').fill('94102');
    await page.locator('[data-test="continue"]').click();

    await expect(page).toHaveURL(/checkout-step-two/);

    // Overview page must list the backpack
    await expect(page.getByText('Sauce Labs Backpack')).toBeVisible();

    // Finish the order — <button data-test="finish">
    await page.locator('[data-test="finish"]').click();

    // Confirmation page
    await expect(page).toHaveURL(/checkout-complete/);
    await expect(page.getByText(/thank you for your order/i)).toBeVisible();

    // Screenshot as evidence
    await page.screenshot({ path: 'test-results/checkout-complete.png' });
  });
});

// ─── Edge case: locked-out user ──────────────────────────────────────────────

test.describe('Edge case: locked_out_user cannot log in', () => {
  test('should show a visible error for locked_out_user', async ({ page }) => {
    await login(page, LOCKED_USER, PASSWORD);

    // Should NOT have navigated away from the login page
    await expect(page).not.toHaveURL(/inventory/);

    // An error container must be visible with an appropriate message
    const error = page.locator('[data-test="error"]');
    await expect(error).toBeVisible();
    await expect(error).toContainText(/locked out/i);
  });
});

// ─── Edge case: remove item from cart before checkout ────────────────────────
//
// PR: feat(ui-qa) — "Remove item from cart before checkout" edge case
//
// This spec was generated to cover the new workflow step added in the PR.
// It guards against regressions where the remove action updates server state
// but the UI fails to re-render the empty-cart state.

test.describe('Edge case: Remove item from cart before checkout', () => {
  test('should correctly reflect an empty cart after removing the Sauce Labs Backpack', async ({ page }) => {
    await login(page, STANDARD_USER, PASSWORD);
    await expect(page).toHaveURL(/inventory/);

    // Add the Sauce Labs Backpack
    await page.locator('[data-test="add-to-cart-sauce-labs-backpack"]').click();

    // Verify badge shows 1 item
    const badge = page.locator('.shopping_cart_badge');
    await expect(badge).toHaveText('1');

    // Navigate to the cart
    await page.locator('.shopping_cart_link').click();
    await expect(page).toHaveURL(/cart/);

    // The item must be present before we remove it
    await expect(page.getByText('Sauce Labs Backpack')).toBeVisible();

    // Remove the item from the cart — <button data-test="remove-sauce-labs-backpack">
    await page.locator('[data-test="remove-sauce-labs-backpack"]').click();

    // After removal: the Backpack must no longer appear in the item list
    await expect(page.getByText('Sauce Labs Backpack')).not.toBeVisible();

    // After removal: the badge must disappear entirely (only rendered when count > 0)
    await expect(badge).not.toBeVisible();

    // The Checkout button must still be visible with an empty cart —
    // it is rendered as <button data-test="checkout"> regardless of cart state
    await expect(page.locator('[data-test="checkout"]')).toBeVisible();

    await page.screenshot({ path: 'test-results/empty-cart-after-remove.png' });
  });
});
