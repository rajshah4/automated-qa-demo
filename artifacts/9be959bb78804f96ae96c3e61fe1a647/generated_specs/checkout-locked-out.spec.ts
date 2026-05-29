/**
 * Edge Case: Locked-Out User Login Failure
 *
 * Source of truth: scenarios/03_ui_workflow/workflow.md — Edge cases section
 * System under test: https://www.saucedemo.com/v1/
 *
 * This spec covers the `locked_out_user` account, which SauceDemo ships as a
 * deliberate failure fixture.  The acceptance criterion is simple: submitting
 * valid credentials for a locked account must show a human-readable error
 * message and keep the user on the login page.
 *
 * Why this edge case?
 *   - It exercises the authentication error-handling path that the happy-path
 *     spec never reaches.
 *   - The error message is rendered in an <h3> with data-test="error", which
 *     lets us verify *both* visibility and message text without relying on
 *     brittle CSS classes.
 *   - Unlike the performance_glitch_user or problem_user cases, the
 *     locked-out scenario gives a clear, deterministic signal (error text)
 *     rather than a subjective timing or visual assertion.
 */

import { test, expect } from '@playwright/test';

const BASE_URL = 'https://www.saucedemo.com/v1/';

test.describe('Authentication edge case: locked-out user', () => {
  test('locked_out_user sees a clear error message and stays on the login page', async ({
    page,
  }) => {
    await page.goto(BASE_URL, { waitUntil: 'networkidle' });

    // Fill credentials using placeholder-based queries (site has no <label> elements)
    await page.getByPlaceholder('Username').fill('locked_out_user');
    await page.getByPlaceholder('Password').fill('secret_sauce');

    // Submit via the login button (input[type=submit] has implicit role "button")
    await page.getByRole('button', { name: 'Login' }).click();

    // The page must NOT navigate away from the login URL
    await expect(page).toHaveURL(/saucedemo\.com/);
    await expect(page).not.toHaveURL(/inventory/);

    // The error container renders an <h3> with the rejection message.
    // getByText checks the visible text of any element, so the <h3> wrapper and
    // its embedded close-button SVG do not interfere with the assertion.
    await expect(
      page.getByText(/sorry, this user has been locked out/i)
    ).toBeVisible();

    // Verify the username field still shows the entered value so the user can
    // correct a typo without re-typing the whole username.
    await expect(page.getByPlaceholder('Username')).toHaveValue('locked_out_user');
  });
});
