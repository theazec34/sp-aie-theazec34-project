import { expect, test } from "@playwright/test";

test("home renders main sections and menu cards", async ({ page }) => {
  await page.goto("/");

  await expect(page.getByRole("heading", { name: /la experiencia comienza aqu[ií]/i })).toBeVisible();
  await expect(page.locator("#carta")).toBeVisible();
  await expect(page.locator("#como-funciona")).toBeVisible();
  await expect(page.locator("#testimonios")).toBeVisible();

  const menuCards = page.locator(".plato-card");
  await expect(menuCards.first()).toBeVisible();
  expect(await menuCards.count()).toBeGreaterThan(0);
});

test("mobile menu opens and closes with keyboard escape", async ({ page }) => {
  await page.setViewportSize({ width: 390, height: 844 });
  await page.goto("/");

  const openButton = page.getByRole("button", { name: /abrir men[uú]/i });
  await openButton.click();
  await expect(page.locator("#mobile-menu")).toHaveClass(/open/);

  await page.keyboard.press("Escape");
  await expect(page.locator("#mobile-menu")).not.toHaveClass(/open/);
});
