/**
 * Shared helpers for e2e tests.
 * All tests mock the backend via page.route() — no real server required.
 */
import { Page } from "@playwright/test";

export const TEST_TOKEN = "e2e-test-token";
export const TEST_USER = { id: "11111111-1111-1111-1111-111111111111", username: "e2euser" };
export const TEST_APP_ID = "aaaaaaaa-0000-0000-0000-000000000001";
export const TEST_COMPANY_ID = "cccccccc-0000-0000-0000-000000000001";

/** Inject a JWT token into localStorage so useAuth() sees an authenticated user. */
export async function setAuthToken(page: Page) {
  await page.addInitScript((token) => {
    localStorage.setItem("token", token);
  }, TEST_TOKEN);
}

/** Mock the /api/auth/me endpoint so useAuth() resolves immediately. */
export async function mockAuthMe(page: Page) {
  await page.route("**/api/auth/me", (route) =>
    route.fulfill({ json: TEST_USER })
  );
}

/** Stub GET /api/stats with zero data. */
export async function mockStats(page: Page) {
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
}

export function makeApp(overrides: Record<string, unknown> = {}) {
  return {
    id: TEST_APP_ID,
    user_id: TEST_USER.id,
    company_id: TEST_COMPANY_ID,
    role_template_id: null,
    job_title: "Software Engineer",
    job_description: "Write great software",
    email_subject: "Let's talk",
    email_body: "I built things.",
    email_status: "confirmed",
    status: "ready",
    notes: null,
    linkedin_note: "Hey, I'd love to connect.",
    contact_count: 2,
    created_at: "2026-03-30T00:00:00",
    updated_at: "2026-03-30T00:00:00",
    ...overrides,
  };
}
