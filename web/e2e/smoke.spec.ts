import { expect, test } from '@playwright/test';

test('app shell renders and the counter increments', async ({ page }) => {
  await page.goto('/');
  await expect(page.getByRole('heading', { name: 'RegWatch' })).toBeVisible();
  const button = page.getByRole('button');
  await button.click();
  await expect(button).toHaveText(/count is 1/);
});
