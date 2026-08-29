import { test, expect } from "@playwright/test";

test("home dashboard loads", async ({ page }) => {
  await page.goto("/");
  await expect(page.getByRole("heading", { name: /learn next/i })).toBeVisible();
});

test("settings asks which API", async ({ page }) => {
  await page.goto("/settings");
  await expect(page.getByRole("heading", { name: /which api/i })).toBeVisible();
  await expect(page.getByText(/Demo/)).toBeVisible();
});

test("twins do not claim actual runs", async ({ page }) => {
  await page.goto("/twins");
  await expect(page.getByText(/SIMULATION/)).toBeVisible();
});
