import { expect, test } from "@playwright/test";

test("home shows hero, featured carta and CTAs", async ({ page }) => {
  await page.goto("/");

  await expect(page.getByRole("heading", { level: 1 })).toContainText(
    "El fuego nos une"
  );
  await expect(page.locator("#carta")).toBeVisible();
  await expect(page.getByRole("link", { name: /Reservar mesa/i }).first()).toBeVisible();
  await expect(page.getByRole("link", { name: /Ver carta completa/i })).toBeVisible();
});

test("navigation reaches employment form", async ({ page }) => {
  await page.goto("/trabaja-con-nosotros");
  await expect(page.locator("#aplicar")).toBeVisible();
});
