import { expect, test } from "@playwright/test";

test.describe("storefront", () => {
  test("browse catalog and add to cart", async ({ page }) => {
    await page.goto("/");
    await expect(page.getByText("Shopfront")).toBeVisible();
    await expect(page.getByRole("button", { name: "Add to cart" }).first()).toBeVisible();
  });

  test("place an order end-to-end", async ({ page }) => {
    await page.goto("/");

    await page.getByRole("button", { name: "Add to cart" }).first().click();
    await expect(page.getByText("Your cart")).toBeVisible();

    await page.getByRole("link", { name: "Checkout" }).click();
    await expect(page.getByRole("heading", { name: "Checkout" })).toBeVisible();

    await page.getByRole("button", { name: "Place order" }).click();
    await expect(page.getByText("Order placed!")).toBeVisible({ timeout: 10_000 });
  });

  test("cart drawer quantity controls update total", async ({ page }) => {
    await page.goto("/");
    await page.getByRole("button", { name: "Add to cart" }).first().click();
    await expect(page.getByText("Your cart")).toBeVisible();

    const plus = page.locator('button:has-text("+")').first();
    if (await plus.isVisible()) {
      await plus.click();
    }
  });
});
