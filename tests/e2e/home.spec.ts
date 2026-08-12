import { expect, test } from "@playwright/test";

test("home renders brand, hero and carta", async ({ page }) => {
  await page.goto("/");

  await expect(page.getByRole("link", { name: /brasaland inicio/i })).toBeVisible();
  await expect(
    page.getByRole("heading", { name: /el sabor de sudamerica/i })
  ).toBeVisible();
  await expect(page.locator("#carta")).toBeVisible();
  await expect(page.getByRole("heading", { name: /carta completa brasaland/i })).toBeVisible();
});

test("nav jumps to galeria and formulario sections", async ({ page }) => {
  await page.goto("/");

  await page.getByRole("navigation", { name: /navegacion principal/i }).getByRole("link", { name: /^fotos$/i }).click();
  await expect(page.locator("#galeria")).toBeVisible();

  await page.getByRole("navigation", { name: /navegacion principal/i }).getByRole("link", { name: /^formulario$/i }).click();
  await expect(page.locator("#aplicar")).toBeVisible();
});
