/**
 * Auth flow — login, register, logout.
 * Backend is fully mocked.
 */
import { test, expect } from "@playwright/test";

const FAKE_TOKEN = "fake-jwt-token-for-e2e";

test.describe("Auth", () => {
  test("shows login form when unauthenticated", async ({ page }) => {
    // Block auth/me so it fails (no token in storage)
    await page.route("**/api/auth/me", (route) => route.fulfill({ status: 401, json: { detail: "Not authenticated" } }));
    await page.goto("/");
    await expect(page.getByRole("heading", { name: /sign in|log in|welcome/i })).toBeVisible();
    await expect(page.getByRole("button", { name: /sign in|log in/i })).toBeVisible();
  });

  test("successful login redirects to dashboard", async ({ page }) => {
    await page.route("**/api/auth/login", (route) =>
      route.fulfill({ json: { access_token: FAKE_TOKEN } })
    );
    await page.route("**/api/auth/me", (route) =>
      route.fulfill({ json: { id: "uid-1", username: "devanshu" } })
    );
    await page.route("**/api/stats", (route) =>
      route.fulfill({ json: { total_applications: 0, total_outreach: 0, total_sent: 0, total_replied: 0, response_rate: 0 } })
    );

    await page.goto("/");
    await page.getByPlaceholder(/username/i).fill("devanshu");
    await page.getByPlaceholder(/password/i).fill("secret");
    await page.getByRole("button", { name: /sign in|log in/i }).click();

    // After login, dashboard should be visible
    await expect(page).toHaveURL("/");
    await expect(page.getByText("devanshu")).toBeVisible();
  });

  test("wrong password shows error", async ({ page }) => {
    await page.route("**/api/auth/login", (route) =>
      route.fulfill({ status: 401, json: { detail: "Invalid credentials" } })
    );
    await page.route("**/api/auth/me", (route) =>
      route.fulfill({ status: 401, json: {} })
    );

    await page.goto("/");
    await page.getByPlaceholder(/username/i).fill("devanshu");
    await page.getByPlaceholder(/password/i).fill("wrongpassword");
    await page.getByRole("button", { name: /sign in|log in/i }).click();

    // Should stay on login page (no redirect)
    await expect(page.getByRole("button", { name: /sign in|log in/i })).toBeVisible();
  });

  test("register creates account and logs in", async ({ page }) => {
    await page.route("**/api/auth/register", (route) =>
      route.fulfill({ json: { access_token: FAKE_TOKEN } })
    );
    await page.route("**/api/auth/me", (route) =>
      route.fulfill({ json: { id: "uid-new", username: "newuser" } })
    );
    await page.route("**/api/stats", (route) =>
      route.fulfill({ json: { total_applications: 0, total_outreach: 0, total_sent: 0, total_replied: 0, response_rate: 0 } })
    );

    await page.goto("/");
    // Switch to register tab/mode
    const registerTab = page.getByRole("tab", { name: /register|sign up|create/i });
    if (await registerTab.isVisible()) {
      await registerTab.click();
    }
    await page.getByPlaceholder(/username/i).fill("newuser");
    await page.getByPlaceholder(/password/i).fill("newpassword");
    await page.getByRole("button", { name: /register|sign up|create/i }).click();

    await expect(page.getByText("newuser")).toBeVisible();
  });

  test("logout clears session and returns to login", async ({ page }) => {
    await page.addInitScript((token) => localStorage.setItem("token", token), FAKE_TOKEN);
    await page.route("**/api/auth/me", (route) =>
      route.fulfill({ json: { id: "uid-1", username: "devanshu" } })
    );
    await page.route("**/api/stats", (route) =>
      route.fulfill({ json: { total_applications: 0, total_outreach: 0, total_sent: 0, total_replied: 0, response_rate: 0 } })
    );

    await page.goto("/");
    await expect(page.getByText("devanshu")).toBeVisible();

    // Find and click logout
    await page.getByRole("button", { name: /logout|sign out|log out/i }).click();

    await expect(page.getByRole("button", { name: /sign in|log in/i })).toBeVisible();
  });
});
