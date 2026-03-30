/**
 * New Outreach Wizard — 5-step flow.
 * Expensive calls (draft-email, find-contacts) are fully mocked.
 */
import { test, expect } from "@playwright/test";
import { setAuthToken, mockAuthMe, TEST_APP_ID, TEST_COMPANY_ID, makeApp } from "./helpers";

const TEMPLATES = [
  {
    id: "tmpl-1",
    user_id: "uid",
    slug: "swe",
    title: "Software Engineer",
    color: "#3b82f6",
    tagline: "Eval framework first.",
    system_prompt: "",
    role_prompt_addition: "ROLE: SWE",
    example_email: null,
    sort_order: 0,
  },
  {
    id: "tmpl-2",
    user_id: "uid",
    slug: "backend",
    title: "Backend Engineer",
    color: "#10b981",
    tagline: "Systems that scale.",
    system_prompt: "",
    role_prompt_addition: "ROLE: Backend",
    example_email: null,
    sort_order: 1,
  },
];

const DRAFT_APP = makeApp({
  email_status: "draft",
  status: "drafting",
  email_subject: "Built an eval framework, cut test debt 40%",
  email_body: "Your team's work on distributed tracing caught my eye.",
});

const CONTACTS = [
  {
    id: "contact-1",
    company_id: TEST_COMPANY_ID,
    first_name: "John",
    last_name: "Doe",
    title: "Engineering Manager",
    seniority: "manager",
    email: "john@stripe.com",
    email_status: "verified",
    linkedin_url: null,
  },
  {
    id: "contact-2",
    company_id: TEST_COMPANY_ID,
    first_name: "Sarah",
    last_name: "Kim",
    title: "Senior Engineer",
    seniority: "senior",
    email: "sarah@stripe.com",
    email_status: "verified",
    linkedin_url: null,
  },
];

test.beforeEach(async ({ page }) => {
  await setAuthToken(page);
  await mockAuthMe(page);

  // Companies
  await page.route("**/api/companies*", (route) => {
    if (route.request().method() === "POST") {
      route.fulfill({
        json: {
          id: TEST_COMPANY_ID,
          name: "Stripe",
          domain: "stripe.com",
          location: "San Francisco, CA",
          apollo_org_id: null,
          employee_count: 8000,
          industry: "FinTech",
          website: null,
        },
      });
    } else {
      route.fulfill({ json: [] });
    }
  });

  // Applications
  await page.route("**/api/applications", (route) => {
    if (route.request().method() === "POST") {
      route.fulfill({ json: DRAFT_APP });
    } else {
      route.fulfill({ json: [] });
    }
  });

  // Templates
  await page.route("**/api/templates*", (route) =>
    route.fulfill({ json: TEMPLATES })
  );

  // Draft email (mocked — not calling real Claude)
  await page.route(`**/api/applications/${TEST_APP_ID}/draft-email`, (route) =>
    route.fulfill({
      json: {
        ...DRAFT_APP,
        email_subject: "Built an eval framework, cut test debt 40%",
        email_body: "Your team's work on distributed tracing caught my eye. I built OpenCodeIntel (87.5% Hit@1, used by Cursor/Windsurf). Available immediately on OPT.",
        email_status: "draft",
      },
    })
  );

  // PUT application (confirm draft, save linkedin_note, status updates)
  await page.route(`**/api/applications/${TEST_APP_ID}`, (route) => {
    if (route.request().method() === "PUT") {
      route.fulfill({ json: makeApp({ email_status: "confirmed", status: "ready" }) });
    } else {
      route.fulfill({ json: DRAFT_APP });
    }
  });

  // Find contacts (mocked — not calling real Apollo)
  await page.route(`**/api/applications/${TEST_APP_ID}/find-contacts`, (route) =>
    route.fulfill({ json: CONTACTS })
  );

  // Apollo credits
  await page.route("**/api/apollo/credits", (route) =>
    route.fulfill({
      json: {
        daily_used: 7,
        daily_limit: 50,
        daily_remaining: 43,
        monthly_used: 234,
        monthly_total: 2515,
        monthly_remaining: 2281,
        max_per_search: 5,
      },
    })
  );

  // Outreach
  await page.route("**/api/outreach*", (route) => {
    if (route.request().method() === "POST") {
      route.fulfill({
        json: {
          id: "outreach-1",
          application_id: TEST_APP_ID,
          contact_id: "contact-1",
          user_id: "uid",
          personalized_greeting: "Hi John,",
          sent_at: null,
          replied: false,
        },
      });
    } else {
      route.fulfill({ json: [] });
    }
  });

  // Profile (needed for wizard)
  await page.route("**/api/profiles*", (route) =>
    route.fulfill({
      json: {
        id: "profile-1",
        user_id: "uid",
        full_name: "Devanshu Chicholikar",
        background: "MS SWE Northeastern",
        projects: [],
        sign_off_block: "Best,\nDevanshu",
        links_block: "github.com/devanshu",
      },
    })
  );
});

test.describe("Outreach Wizard", () => {
  test("step 1: company + job input renders", async ({ page }) => {
    await page.goto("/outreach/new");
    await expect(page.getByPlaceholder(/company/i)).toBeVisible();
    await expect(page.getByPlaceholder(/job title/i)).toBeVisible();
  });

  test("step 1 → step 2: fills details and advances", async ({ page }) => {
    await page.goto("/outreach/new");

    await page.getByPlaceholder(/company/i).fill("Stripe");
    await page.getByPlaceholder(/location/i).fill("San Francisco, CA");
    await page.getByPlaceholder(/job title/i).fill("Software Engineer");
    await page.getByPlaceholder(/job description/i).fill("Build distributed systems at scale.");

    await page.getByRole("button", { name: /next|continue/i }).click();

    // Should now see template selection
    await expect(page.getByText("Software Engineer").first()).toBeVisible();
  });

  test("step 2: template cards displayed", async ({ page }) => {
    await page.goto("/outreach/new");

    // Fill step 1
    await page.getByPlaceholder(/company/i).fill("Stripe");
    await page.getByPlaceholder(/location/i).fill("San Francisco, CA");
    await page.getByPlaceholder(/job title/i).fill("Software Engineer");
    await page.getByPlaceholder(/job description/i).fill("Build distributed systems at scale.");
    await page.getByRole("button", { name: /next|continue/i }).click();

    // Templates visible
    await expect(page.getByText("Software Engineer")).toBeVisible();
    await expect(page.getByText("Backend Engineer")).toBeVisible();
  });

  test("step 3: draft email renders subject and body", async ({ page }) => {
    await page.goto("/outreach/new");

    // Step 1
    await page.getByPlaceholder(/company/i).fill("Stripe");
    await page.getByPlaceholder(/location/i).fill("San Francisco, CA");
    await page.getByPlaceholder(/job title/i).fill("Software Engineer");
    await page.getByPlaceholder(/job description/i).fill("Build distributed systems at scale.");
    await page.getByRole("button", { name: /next|continue/i }).click();

    // Step 2 — pick template
    await page.getByText("Software Engineer").first().click();
    await page.getByRole("button", { name: /next|continue|draft/i }).click();

    // Step 3 — draft visible
    await expect(page.getByText(/eval framework|distributed tracing/i)).toBeVisible();
  });

  test("step 4: contacts step shows Apollo credits", async ({ page }) => {
    await page.goto("/outreach/new");

    // Step 1
    await page.getByPlaceholder(/company/i).fill("Stripe");
    await page.getByPlaceholder(/location/i).fill("San Francisco, CA");
    await page.getByPlaceholder(/job title/i).fill("Software Engineer");
    await page.getByPlaceholder(/job description/i).fill("Build distributed systems at scale.");
    await page.getByRole("button", { name: /next|continue/i }).click();

    // Step 2
    await page.getByText("Software Engineer").first().click();
    await page.getByRole("button", { name: /next|continue|draft/i }).click();

    // Step 3 — confirm draft
    const confirmBtn = page.getByRole("button", { name: /confirm|next|continue/i });
    await confirmBtn.click();

    // Step 4 — contacts + credits
    await expect(page.getByText(/apollo|credits|today/i)).toBeVisible();
    await expect(page.getByRole("button", { name: /search apollo/i })).toBeEnabled();
  });

  test("step 4: search apollo shows contacts", async ({ page }) => {
    await page.goto("/outreach/new");

    // Step 1
    await page.getByPlaceholder(/company/i).fill("Stripe");
    await page.getByPlaceholder(/location/i).fill("San Francisco, CA");
    await page.getByPlaceholder(/job title/i).fill("Software Engineer");
    await page.getByPlaceholder(/job description/i).fill("Build distributed systems at scale.");
    await page.getByRole("button", { name: /next|continue/i }).click();

    // Step 2
    await page.getByText("Software Engineer").first().click();
    await page.getByRole("button", { name: /next|continue|draft/i }).click();

    // Step 3
    await page.getByRole("button", { name: /confirm|next|continue/i }).click();

    // Step 4 — search
    await page.getByRole("button", { name: /search apollo/i }).click();

    await expect(page.getByText("John Doe")).toBeVisible();
    await expect(page.getByText("Sarah Kim")).toBeVisible();
  });

  test("step 5: send step has per-contact copy buttons", async ({ page }) => {
    await page.goto("/outreach/new");

    // Step 1
    await page.getByPlaceholder(/company/i).fill("Stripe");
    await page.getByPlaceholder(/location/i).fill("San Francisco, CA");
    await page.getByPlaceholder(/job title/i).fill("Software Engineer");
    await page.getByPlaceholder(/job description/i).fill("Build distributed systems at scale.");
    await page.getByRole("button", { name: /next|continue/i }).click();

    // Step 2
    await page.getByText("Software Engineer").first().click();
    await page.getByRole("button", { name: /next|continue|draft/i }).click();

    // Step 3
    await page.getByRole("button", { name: /confirm|next|continue/i }).click();

    // Step 4 — search, then proceed
    await page.getByRole("button", { name: /search apollo/i }).click();
    await expect(page.getByText("John Doe")).toBeVisible();
    await page.getByRole("button", { name: /next|send|continue/i }).click();

    // Step 5 — copy buttons per contact
    await expect(page.getByText("John Doe")).toBeVisible();
    await expect(page.getByRole("button", { name: /copy|subject|body|full email/i }).first()).toBeVisible();
  });
});
