import { expect, test } from "@playwright/test";

test("application form shows validation when submitted empty", async ({ page }) => {
  await page.goto("/#aplicar");

  const formSection = page.locator("#aplicar");
  await expect(formSection).toBeVisible({ timeout: 20000 });

  await formSection.getByRole("button", { name: /enviar aplicacion/i }).click();

  await expect(formSection.locator(".error-summary")).toBeVisible({ timeout: 10000 });
  await expect(formSection).toContainText(/el nombre es obligatorio/i);
  await expect(formSection).toContainText(/el correo electronico es obligatorio/i);
});
