import { PlaywrightTestConfig } from "@playwright/test";

const config: PlaywrightTestConfig = {
  testDir: "./tests/e2e",
  use: { baseURL: process.env.BASE_URL || "http://127.0.0.1:3000", headless: true },
  webServer: undefined,
};
export default config;
