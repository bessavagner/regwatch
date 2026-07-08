import { expect, test } from '@playwright/test';

// Requires a running same-origin stack (Vite proxying /api to a Django dev server
// seeded with an invite_user account). Credentials come from env so nothing is hardcoded.
const USER = process.env.E2E_USER ?? 'e2e@firm.com';
const PASS = process.env.E2E_PASS ?? 'e2epw12345';

test('rejects bad credentials, accepts a valid login, then logs out', async ({ page }) => {
  await page.goto('/login');

  await page.getByLabel(/username/i).fill(USER);
  await page.getByLabel(/password/i).fill('wrong-password');
  await page.getByRole('button', { name: /sign in/i }).click();
  await expect(page.getByRole('alert')).toBeVisible();

  await page.getByLabel(/password/i).fill(PASS);
  await page.getByRole('button', { name: /sign in/i }).click();
  await expect(page).toHaveURL(/\/feed/);
});
