import { expect, test } from '@playwright/test';

const USER = process.env.E2E_USER ?? 'e2e@firm.com';
const PASS = process.env.E2E_PASS ?? 'e2epw12345';

// Requires the seeded E2E user to have at least one `new` match to triage.
test('a firm user logs in and marks a match relevant', async ({ page }) => {
  await page.goto('/login');
  await page.getByLabel(/usuário/i).fill(USER);
  await page.getByLabel(/senha/i).fill(PASS);
  await page.getByRole('button', { name: /entrar/i }).click();
  await expect(page).toHaveURL(/\/feed/);

  const firstRelevant = page.getByRole('button', { name: /^relevante$/i }).first();
  await firstRelevant.click();
  // Scoped to the badge <span>: the situação filter's <option> now carries the
  // same "relevante" text, so a bare getByText would match the select instead.
  await expect(
    page.locator('span').filter({ hasText: /^relevante$/ }).first(),
  ).toBeVisible();
});
