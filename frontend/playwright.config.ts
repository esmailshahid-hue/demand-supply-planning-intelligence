import { defineConfig } from '@playwright/test';
export default defineConfig({
  testDir: './e2e', timeout: 30_000, workers: 1,
  use: { baseURL: 'http://127.0.0.1:8000', headless: true,
    launchOptions: process.env.CHROME_PATH ? { executablePath: process.env.CHROME_PATH } : {},
  },
  webServer: { command: '../scripts/start.sh', url: 'http://127.0.0.1:8000/api/health', reuseExistingServer: !process.env.CI, timeout: 30_000 },
});
