import { expect, test } from "@playwright/test";

test("job application form validates required fields", async ({ page }) => {
  await page.goto("/trabaja-con-nosotros");

  const form = page.locator("#aplicar");
  await expect(form).toBeVisible();

  await form.getByRole("button", { name: /Enviar candidatura/i }).click();
  await expect(form.getByText(/nombre es obligatorio/i)).toBeVisible();
});
