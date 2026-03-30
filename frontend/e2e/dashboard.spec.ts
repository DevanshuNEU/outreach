/**
 * Dashboard — stats display.
 */
import { test, expect } from "@playwright/test";
import { setAuthToken, mockAuthMe } from "./helpers";

test.beforeEach(async ({ page }) => {
  await setAuthToken(page);
  await mockAuthMe(page);
});

test.describe("Dashboard", () => {
  test("shows zero stats when no data", async ({ page }) => {
    await page.route("**/api/stats", (route) =>
      route.fulfill({
        json: {
          total_applications: 0,
          total_outreach: 0,
          total_sent: 0,
          total_replied: 0,
          response_rate: 0,
        },
      })
    );
    await page.goto("/");
    // Stats cards should show 0 values
    await expect(page.getByText("0").first()).toBeVisible();
  });

  test("shows real stats", async ({ page }) => {
    await page.route("**/api/stats", (route) =>
      route.fulfill({
        json: {
          total_applications: 12,
          total_outreach: 30,
          total_sent: 25,
          total_replied: 5,
          response_rate: 20.0,
        },
      })
    );
    await page.goto("/");
    await expect(page.getByText("12")).toBeVisible();
    await expect(page.getByText("25")).toBeVisible();
    await expect(page.getByText("5")).toBeVisible();
  });

  test("New Outreach button navigates to wizard", async ({ page }) => {
    await page.route("**/api/stats", (route) =>
      route.fulfill({ json: { total_applications: 0, total_outreach: 0, total_sent: 0, total_replied: 0, response_rate: 0 } })
    );
    await page.goto("/");
    await page.getByRole("link", { name: /new outreach|start outreach|new application/i }).click();
    await expect(page).toHaveURL("/outreach/new");
  });
});
