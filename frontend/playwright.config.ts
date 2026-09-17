import { defineConfig } from '@playwright/test';
const baseURL = `http://127.0.0.1:${process.env.PORT || '8000'}`;
export default defineConfig({
  testDir: './e2e', timeout: 30_000, workers: 1,
  use: { baseURL, headless: true,
    launchOptions: process.env.CHROME_PATH ? { executablePath: process.env.CHROME_PATH } : {},
  },
  webServer: { command: '../scripts/start.sh', url: `${baseURL}/api/health`, reuseExistingServer: !process.env.CI, timeout: 30_000 },
});
