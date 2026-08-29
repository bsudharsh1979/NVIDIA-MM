import { test, expect } from "@playwright/test";

test("walkthrough player open play next prev jump depth close", async ({ page }) => {
  await page.goto("/notebooks/02a_Intermediate_Fusion?walkthrough=1");
  await expect(page.getByText(/Audio lecture/i)).toBeVisible({ timeout: 30000 });
  const play = page.getByRole("button", { name: /^Play$/i });
  if (await play.isVisible()) await play.click();
  await page.getByRole("button", { name: /^Next$/i }).click();
  await page.getByRole("button", { name: /^Prev$/i }).click();
  await page.getByRole("button", { name: /The game plan/i }).click();
  await page.getByRole("button", { name: /EXPERT/i }).click();
  await expect(page.getByText(/Audio lecture/i)).toBeVisible();
  await page.getByRole("button", { name: /Close/i }).click();
  await expect(page.getByRole("button", { name: /Play audio lecture/i })).toBeVisible();
});
