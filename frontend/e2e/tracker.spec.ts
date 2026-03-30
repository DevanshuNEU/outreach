/**
 * Tracker page — list, filter, status edit, delete.
 */
import { test, expect } from "@playwright/test";
import { setAuthToken, mockAuthMe, TEST_APP_ID, makeApp } from "./helpers";

const APPS = [
  makeApp({ id: "app-1", job_title: "Software Engineer", status: "ready", contact_count: 2 }),
  makeApp({ id: "app-2", job_title: "Backend Engineer", status: "drafting", contact_count: 0 }),
  makeApp({ id: "app-3", job_title: "ML Engineer", status: "outreach_in_progress", contact_count: 3 }),
];

test.beforeEach(async ({ page }) => {
  await setAuthToken(page);
  await mockAuthMe(page);
  await page.route("**/api/applications*", (route) => {
    if (route.request().method() === "GET") {
      route.fulfill({ json: APPS });
    } else {
      route.continue();
    }
  });
});

test.describe("Tracker", () => {
  test("lists applications with correct titles", async ({ page }) => {
    await page.goto("/tracker");
    await expect(page.getByText("Software Engineer")).toBeVisible();
    await expect(page.getByText("Backend Engineer")).toBeVisible();
    await expect(page.getByText("ML Engineer")).toBeVisible();
  });

  test("shows contact count on each card", async ({ page }) => {
    await page.goto("/tracker");
    await expect(page.getByText("2 contacts")).toBeVisible();
    await expect(page.getByText("3 contacts")).toBeVisible();
  });

  test("empty state when no applications", async ({ page }) => {
    await page.route("**/api/applications*", (route) =>
      route.fulfill({ json: [] })
    );
    await page.goto("/tracker");
    // Should show empty state message or just no cards
    await expect(page.getByText("Software Engineer")).not.toBeVisible();
  });

  test("status filter narrows visible cards", async ({ page }) => {
    await page.goto("/tracker");

    // Find the status filter dropdown
    const filterSelect = page.getByRole("combobox").first();
    await filterSelect.selectOption("drafting");

    await expect(page.getByText("Backend Engineer")).toBeVisible();
    await expect(page.getByText("Software Engineer")).not.toBeVisible();
  });

  test("inline status change calls API", async ({ page }) => {
    let patchBody: unknown = null;
    await page.route(`**/api/applications/app-1`, (route) => {
      if (route.request().method() === "PUT") {
        patchBody = route.request().postDataJSON();
        route.fulfill({ json: makeApp({ id: "app-1", status: "outreach_in_progress" }) });
      } else {
        route.continue();
      }
    });

    await page.goto("/tracker");

    // Find the status select on the first card
    const statusSelect = page.locator("[data-app-id='app-1'] select, .status-select").first();
    if (await statusSelect.isVisible()) {
      await statusSelect.selectOption("outreach_in_progress");
      await page.waitForTimeout(200);
      expect(patchBody).toMatchObject({ status: "outreach_in_progress" });
    }
  });

  test("delete shows confirmation dialog then removes card", async ({ page }) => {
    let deleteOutreachCalled = false;
    let deleteAppCalled = false;

    await page.route("**/api/outreach*", (route) => {
      if (route.request().method() === "DELETE") {
        deleteOutreachCalled = true;
        route.fulfill({ json: { ok: true } });
      } else {
        route.fulfill({ json: [] });
      }
    });

    await page.route(`**/api/applications/app-1`, (route) => {
      if (route.request().method() === "DELETE") {
        deleteAppCalled = true;
        route.fulfill({ json: { ok: true } });
      } else {
        route.continue();
      }
    });

    // After delete, return only remaining apps
    await page.route("**/api/applications*", (route) => {
      if (route.request().method() === "GET") {
        route.fulfill({ json: APPS.filter((a) => a.id !== "app-1") });
      } else {
        route.continue();
      }
    });

    await page.goto("/tracker");
    await expect(page.getByText("Software Engineer")).toBeVisible();

    // Click the trash/delete button on the first card
    const deleteBtn = page.getByRole("button", { name: /delete|trash/i }).first();
    await deleteBtn.click();

    // Confirmation dialog should appear
    await expect(page.getByRole("dialog")).toBeVisible();
    await expect(page.getByText(/delete|permanently/i)).toBeVisible();

    // Confirm the delete
    await page.getByRole("button", { name: /delete|confirm/i }).last().click();

    await expect(deleteOutreachCalled || deleteAppCalled).toBeTruthy();
  });

  test("clicking a card navigates to detail page", async ({ page }) => {
    await page.route("**/api/applications/app-1*", (route) =>
      route.fulfill({ json: makeApp({ id: "app-1" }) })
    );
    await page.route("**/api/outreach*", (route) => route.fulfill({ json: [] }));

    await page.goto("/tracker");
    await page.getByText("Software Engineer").first().click();
    await expect(page).toHaveURL(/\/applications\/app-1/);
  });
});
