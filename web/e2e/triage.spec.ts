import { expect, test } from '@playwright/test';

const USER = process.env.E2E_USER ?? 'e2e@firm.com';
const PASS = process.env.E2E_PASS ?? 'e2epw12345';

// Requires the seeded E2E user to have at least one `new` match to triage.
test('a firm user logs in and marks a match relevant', async ({ page }) => {
  await page.goto('/login');
  await page.getByLabel(/username/i).fill(USER);
  await page.getByLabel(/password/i).fill(PASS);
  await page.getByRole('button', { name: /sign in/i }).click();
  await expect(page).toHaveURL(/\/feed/);

  const firstRelevant = page.getByRole('button', { name: /relevant/i }).first();
  await firstRelevant.click();
  // Exact, case-sensitive match: the state badge renders the raw lowercase
  // "relevant" value, while the (hidden) State filter <option> reads "Relevant".
  await expect(page.getByText('relevant', { exact: true }).first()).toBeVisible();
});
