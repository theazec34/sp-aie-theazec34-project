import { expect, test } from "@playwright/test";

test("application page shows validation errors when submitting empty form", async ({ page }) => {
  await page.goto("/application.html");

  await page.getByRole("button", { name: /enviar aplicaci[oó]n/i }).click();

  await expect(page.locator("#error-summary")).toBeVisible();
  await expect(page.locator("#error-list")).toContainText(/el nombre es obligatorio/i);
  await expect(page.locator("#error-list")).toContainText(/el correo electr[oó]nico es obligatorio/i);
});

test("application page has menu link to carta", async ({ page }) => {
  await page.setViewportSize({ width: 390, height: 844 });
  await page.goto("/application.html");

  const menuLink = page.getByRole("link", { name: /ir a la carta/i });
  await expect(menuLink).toHaveAttribute("href", "index.html#carta");
});
