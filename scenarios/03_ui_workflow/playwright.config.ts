import { defineConfig, devices } from '@playwright/test';

export default defineConfig({
  testDir: './generated_specs',
  fullyParallel: false,
  retries: 1,
  reporter: [
    ['html', { outputFolder: 'playwright-report', open: 'never' }],
    ['list'],
  ],
  use: {
    baseURL: 'https://www.saucedemo.com',
    trace: 'on',
    video: 'on',
    screenshot: 'only-on-failure',
    headless: true,
  },
  outputDir: 'test-results',
  projects: [
    {
      name: 'chromium',
      use: { ...devices['Desktop Chrome'] },
    },
  ],
});
