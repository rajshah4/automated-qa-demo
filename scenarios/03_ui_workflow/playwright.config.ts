import { defineConfig, devices } from '@playwright/test';

export default defineConfig({
  testDir: './generated_specs',
  fullyParallel: true,
  reporter: [
    ['list'],
    ['html', { outputFolder: 'playwright-report', open: 'never' }],
  ],
  use: {
    trace: 'on',                  // time-travel debugging for every test
    video: 'on',                  // per-test video
    screenshot: 'only-on-failure',
    actionTimeout: 15_000,
  },
  projects: [
    { name: 'chromium', use: { ...devices['Desktop Chrome'] } },
  ],
});
