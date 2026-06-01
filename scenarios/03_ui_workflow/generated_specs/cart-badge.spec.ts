/**
 * Edge-case spec: Cart badge increments / decrements correctly
 *
 * Workflow source: scenarios/03_ui_workflow/workflow.md
 * Edge case: "Cart badge increments after adding an item"
 *
 * Why this edge case?
 * -------------------
 * The `.shopping_cart_badge` is the only visible indicator of cart contents
 * on the inventory page. If a refactor of the cart store introduces a bug
 * (wrong count, stale render, badge stays on 0-item cart), this spec catches
 * it immediately without requiring the tester to navigate to the cart page.
 * It also exercises a remove flow that is easy to regress when add/remove
 * share a single event handler.
 *
 * Selector strategy
 * -----------------
 * Same priority as the happy-path spec (getByRole > getByLabel > getByPlaceholder > getByText).
 * The cart badge element (.shopping_cart_badge) has no ARIA role or label —
 * using its CSS class as an intentional fallback with this annotation.
 */

import { test, expect } from '@playwright/test';

const BASE_URL = 'https://www.saucedemo.com/';
const USERNAME  = 'standard_user';
const PASSWORD  = 'secret_sauce';

/** Log in and land on the inventory page. */
async function login(page: import('@playwright/test').Page): Promise<void> {
  await page.goto(BASE_URL);
  await page.getByPlaceholder('Username').fill(USERNAME);
  await page.getByPlaceholder('Password').fill(PASSWORD);
  await page.getByRole('button', { name: /login/i }).click();
  await page.waitForURL('**/inventory.html');
}

test.describe('Cart badge — increment and decrement', () => {
  test('badge is absent before any item is added', async ({ page }) => {
    await login(page);
    // Badge should not exist when cart is empty.
    await expect(page.locator('.shopping_cart_badge')).toHaveCount(0);
  });

  test('badge shows "1" after adding one item', async ({ page }) => {
    await login(page);
    await page.locator('.inventory_item')
      .filter({ hasText: 'Sauce Labs Backpack' })
      .getByRole('button', { name: /add to cart/i })
      .click();
    // .shopping_cart_badge: CSS fallback — no role/label on this span.
    await expect(page.locator('.shopping_cart_badge')).toHaveText('1');
  });

  test('badge increments to "2" after adding a second distinct item', async ({ page }) => {
    await login(page);

    // Add first item.
    await page.locator('.inventory_item')
      .filter({ hasText: 'Sauce Labs Backpack' })
      .getByRole('button', { name: /add to cart/i })
      .click();
    await expect(page.locator('.shopping_cart_badge')).toHaveText('1');

    // Add second item.
    await page.locator('.inventory_item')
      .filter({ hasText: 'Sauce Labs Bike Light' })
      .getByRole('button', { name: /add to cart/i })
      .click();
    await expect(page.locator('.shopping_cart_badge')).toHaveText('2');
  });

  test('badge decrements when an item is removed via the inventory Remove button', async ({ page }) => {
    await login(page);

    // Build up a cart of 2.
    await page.locator('.inventory_item')
      .filter({ hasText: 'Sauce Labs Backpack' })
      .getByRole('button', { name: /add to cart/i })
      .click();
    await page.locator('.inventory_item')
      .filter({ hasText: 'Sauce Labs Bike Light' })
      .getByRole('button', { name: /add to cart/i })
      .click();
    await expect(page.locator('.shopping_cart_badge')).toHaveText('2');

    // Remove one item — button label flips to "Remove" after add.
    await page.locator('.inventory_item')
      .filter({ hasText: 'Sauce Labs Backpack' })
      .getByRole('button', { name: /remove/i })
      .click();
    await expect(page.locator('.shopping_cart_badge')).toHaveText('1');
  });

  test('badge disappears entirely when the last item is removed', async ({ page }) => {
    await login(page);

    // Add one item then remove it.
    await page.locator('.inventory_item')
      .filter({ hasText: 'Sauce Labs Backpack' })
      .getByRole('button', { name: /add to cart/i })
      .click();
    await expect(page.locator('.shopping_cart_badge')).toHaveText('1');

    await page.locator('.inventory_item')
      .filter({ hasText: 'Sauce Labs Backpack' })
      .getByRole('button', { name: /remove/i })
      .click();

    // Badge must be absent (not rendered) when cart is empty again.
    await expect(page.locator('.shopping_cart_badge')).toHaveCount(0);
  });
});
