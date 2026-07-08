import { defineConfig } from '@playwright/test';

// Local e2e runs against a same-origin dev server (Vite proxying /api to Django).
// The deployed smoke overrides PLAYWRIGHT_BASE_URL to the live HTTPS host.
const baseURL = process.env.PLAYWRIGHT_BASE_URL ?? 'http://localhost:5173';

export default defineConfig({
  testDir: './e2e',
  timeout: 30_000,
  use: { baseURL, trace: 'on-first-retry' },
  webServer: process.env.PLAYWRIGHT_BASE_URL
    ? undefined
    : { command: 'npm run dev', url: 'http://localhost:5173', reuseExistingServer: true },
});
