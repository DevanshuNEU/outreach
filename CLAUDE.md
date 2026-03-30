# CLAUDE.md — Job Outreach Platform (Full Context Handoff)

> **READ THIS FIRST BEFORE DOING ANYTHING.**
> This file is the complete brain of this project. Every decision, every fix, every pending task is here. Do not ask Devanshu to re-explain things that are in this file.

---

## WHO YOU ARE TALKING TO

**Devanshu Chicholikar**
- MS Software Engineering Systems, Northeastern University, GPA 3.85, graduating **May 2026**
- F1 visa → OPT → STEM OPT (3 years total work auth, no H1B lottery)
- Email: devanshichi9@gmail.com
- Talks fast, gets frustrated when things are slow or broken, but is sharp
- Does NOT want long explanations. Give him the fix, then a brief reason. Max 3-4 lines per answer unless it's complex
- Calls things "man", gets excited when things work ("Its working!")
- When he says "look into this" with a screenshot — that means something is broken, go fix it immediately
- When he says "I wanna start from starting" — he's frustrated and wants a clean slate approach
- He is building this platform primarily for HIMSELF (job hunting, May 2026 graduation) plus 2 friends (2 SWE, 1 PM)

---

## WHAT WE ARE BUILDING

**Cold outreach job hunting platform.** Three real users, fully independent.

The core workflow:
1. User enters company name + job description
2. AI (Claude Haiku) drafts a personalized cold email using the user's profile + role-specific template
3. Apollo.io API finds verified contacts at that company (recruiters, hiring managers, senior engineers)
4. Platform produces copy-paste ready emails — one per contact, same body, just swap the greeting name
5. User tracks: applications sent, contacts messaged, replies received

**This is NOT a job board scraper. It is a cold outreach tool.** The user finds jobs, pastes the JD, we do the rest.

---

## TECH STACK

| Layer | Tech |
|---|---|
| Frontend | React + Vite + shadcn/ui + Tailwind |
| Backend | FastAPI (Python) on Railway |
| Database | Supabase (Postgres) — service-role key, NO RLS |
| Email AI | Claude Haiku (`claude-haiku-4-5-20251001`) via Anthropic API |
| Contact Search | Apollo.io API (Basic plan, $59/mo) |
| Auth | JWT (python-jose + passlib/bcrypt pinned to 4.0.1) |

---

## PROJECT STRUCTURE

```
/Users/devanshu/Desktop/Job-Outreach/
├── CLAUDE.md                          ← you are here
├── backend/
│   ├── .env                           ← ALL secrets live here
│   ├── requirements.txt
│   └── app/
│       ├── main.py                    ← FastAPI app, CORS, router includes
│       ├── config.py                  ← Settings with load_dotenv(override=True) — CRITICAL
│       ├── database.py                ← Supabase client (service-role key)
│       ├── update_all.py             ← Re-seeds Devanshu's profile + all 8 templates
│       ├── auth/
│       │   ├── router.py             ← /api/auth/register, /api/auth/login
│       │   └── deps.py              ← get_current_user JWT dependency
│       ├── routers/
│       │   ├── contacts.py          ← Apollo search + manual contact entry
│       │   ├── emails.py            ← POST /api/draft-email
│       │   ├── applications.py      ← CRUD for applications
│       │   ├── profiles.py          ← User profile CRUD
│       │   ├── templates.py         ← Role template CRUD
│       │   ├── companies.py         ← Company CRUD
│       │   ├── outreach.py          ← Outreach log
│       │   └── stats.py             ← Dashboard stats
│       ├── services/
│       │   ├── apollo_service.py    ← Apollo people/company search
│       │   └── email_service.py     ← Claude Haiku email drafting
│       └── models/
│           └── schemas.py           ← Pydantic response models
├── frontend/
│   └── src/
│       ├── pages/
│       │   ├── NewOutreachPage.tsx  ← Main 5-step wizard (the core UI)
│       │   ├── DashboardPage.tsx
│       │   └── ...
│       ├── components/
│       │   ├── CopyButton.tsx
│       │   └── ui/                  ← shadcn components
│       └── lib/
│           └── api.ts               ← Axios instance with JWT header
└── supabase/
    └── migrations/
        └── 001_schema.sql           ← Full DB schema
```

---

## DATABASE SCHEMA (Supabase)

**Key tables:**
- `users` — auth (id, email, hashed_password)
- `profiles` — user profile (full_name, background, projects JSON, sign_off_block, links_block)
- `role_templates` — 8 templates per user (slug, title, color, role_prompt_addition, tagline)
- `companies` — cached company data (name, domain, apollo_org_id, employee_count, location, industry)
- `applications` — one per outreach attempt (user_id, company_id, role_template_id, job_title, job_description, email_subject, email_body, status, email_status)
- `contacts` — people found via Apollo or added manually (apollo_person_id UNIQUE, first_name, last_name, title, seniority, email, email_status, linkedin_url, company_id)
- `outreach` — tracks which contact got which email (application_id, contact_id, replied toggle)
- `api_usage` — logs every Anthropic + Apollo API call with token counts and cost

**IMPORTANT:** We use the **service-role key** (bypasses RLS). No RLS is enabled. All user isolation is done in backend code with `.eq("user_id", current_user["id"])` filters.

---

## DEVANSHU'S USER ID

```
193871f2-996c-49fa-9222-402bc3621cb0
```

Used in `update_all.py` to seed his profile and templates.

---

## THE 5-STEP WIZARD (NewOutreachPage.tsx)

1. **Input** — Company name, location, domain (optional), job title, job description
2. **Template** — Pick from 8 role-based templates (swe, ai-ml, fde, context, fullstack, cloud, rag, backend)
3. **Draft** — Claude Haiku writes the email. User can edit subject and body inline. Regenerate button.
4. **Contacts** — "Search Apollo" button hits the API. "Add Manually" form for LinkedIn-sourced contacts.
5. **Send** — Per-contact copy buttons: Subject, Body, Full Email (greeting + body + links + sign-off)

`buildFullEmail(firstName)` assembles: `Hi {firstName},\n\n{body}\n\n{linksBlock}\n\n{signOff}`

---

## APOLLO INTEGRATION

### How it works (TWO-STEP: search is free, enrichment costs credits)
1. `search_company()` — hits `mixed_companies/search` to get Apollo org ID + employee count
2. `_get_company_tier()` — classifies company: startup/growth/midsize/enterprise based on headcount
3. `find_contacts()` runs two steps:
   - **Step 1 (FREE):** `mixed_people/api_search` — finds people candidates, returns obfuscated names + `has_email` flag. NO credits used.
   - **Step 2 (COSTS CREDITS):** `people/bulk_match` with `reveal_personal_emails: true` — enriches up to 10 people per call, returns full name + verified email. ~1 credit per person.
4. Location filtering — `_normalize_location()` converts "San Francisco, CA" → `["San Francisco, California, United States", "San Francisco, CA"]` and passes as `person_locations` filter in Step 1
5. Only candidates with `has_email: true` from Step 1 are sent to enrichment (saves credits)
6. Accepted email statuses: `verified`, `likely`, `guessed`
7. Contacts upserted to DB (shared across users — cached results save credits on repeat searches)

### Credit budget
2,500 credits/month on Basic. ~1 credit per email revealed. If you search 5 companies/day × 10 contacts = 50 credits/day = ~1,500/month. Plenty of headroom.

### API auth
Apollo changed their API. Key must be in **header**, not body:
```python
headers = {"X-Api-Key": settings.apollo_api_key, "Content-Type": "application/json", "Cache-Control": "no-cache"}
```
Endpoint: `POST https://api.apollo.io/api/v1/mixed_people/api_search` (NOT mixed_people/search — that's free plan only. api_search is the paid plan endpoint.)

### Manual contacts
`POST /api/contacts/manual` — for contacts found on LinkedIn. Gets `email_status: "manual"`.

---

## THE .ENV FILE (backend/.env)

```
SUPABASE_URL=https://iuykqluvkanimguteevp.supabase.co
SUPABASE_SERVICE_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Iml1eWtxbHV2a2FuaW1ndXRlZXZwIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc3NDcxNjY3MywiZXhwIjoyMDkwMjkyNjczfQ.FpfW0oTMSoiVshq3xZcN3hWMzdyY-Y8jwQbzaz68zNA
APOLLO_API_KEY=<UPDATE THIS — see Pending Tasks below>
ANTHROPIC_API_KEY=REDACTED_ANTHROPIC_KEY
JWT_SECRET=95dea695d961fefa98fc75842779298552102039b96e587967ce1f01cd5a8e65
CORS_ORIGINS=http://localhost:5173
```

---

## CRITICAL CONFIG FIX (already applied — do not revert)

`backend/app/config.py` has `load_dotenv(override=True)` called BEFORE `Settings()`. This is required because the system has an empty `ANTHROPIC_API_KEY=` env var that was overriding the .env value.

```python
import os
from dotenv import load_dotenv
from pydantic_settings import BaseSettings

load_dotenv(override=True)  # ← THIS LINE IS CRITICAL

class Settings(BaseSettings):
    ...
```

If you ever see draft failing with an Anthropic error, check this first.

---

## KNOWN FIXES ALREADY APPLIED

| Problem | Fix |
|---|---|
| `bcrypt` crash on Python 3.13 | Pinned `bcrypt==4.0.1` in requirements.txt |
| ANTHROPIC_API_KEY loading empty | `load_dotenv(override=True)` in config.py before Settings() |
| Apollo 422 "key must be in X-Api-Key header" | Moved api_key from request body to header |
| Email body 190 words (ignoring limit) | Stricter prompt: "STRICT 120 WORD MAXIMUM. Count before you output." |
| FK constraint when deleting templates | Null `role_template_id` on applications before delete |
| Em dashes in all templates | Replaced with commas/periods/colons throughout update_all.py — ZERO em dashes allowed |
| Apollo returning 403 (free plan key) | User has now purchased Basic plan on devanshichi9@gmail.com — needs new API key |

---

## THE EMAIL VOICE (non-negotiable)

These rules are baked into the system prompt for Claude Haiku:

- **ZERO em dashes.** Period.
- ZERO emojis
- No "passionate", "leverage", "synergy", "rockstar", "ninja", "utilize", "architect (as verb)"
- Never start with "I hope this email finds you well" or "My name is"
- Use contractions: "I'm" not "I am"
- Short sentences. If a sentence has two clauses joined by "and/but" → break it into two
- Max 120 words for body. Hard limit. No exceptions.
- Structure: Hook → Connection → 3 bullets → CTA → Links → Sign-off

---

## DEVANSHU'S PROFILE (what goes in his emails)

**Background highlights:**
- MS SWE @ Northeastern, GPA 3.85, May 2026
- Production e-commerce: profiled before adding servers, found 3 root causes, p95 800ms → 280ms, checkout +18%
- OpenCodeIntel: AST chunking insight (chunking strategy beat every model swap), 87.5% Hit@1, Cursor/Windsurf MCP integration
- Portfolio is a full OS in the browser (not a flex — it's a trap because portfolios bounce in 8 seconds)
- Graduate TA for Cloud Computing, wrote Docker/GitHub Actions/Terraform curriculum for 180+ students
- F1 → OPT → STEM OPT, 3 years work auth, no H1B lottery needed

**8 Templates (slugs):** swe, ai-ml, fde, context, fullstack, cloud, rag, backend

To re-seed profile + all templates:
```bash
cd backend
python -m app.update_all
```

---

## PENDING TASKS (most important first)

### 1. ✅ JUST PURCHASED — Update Apollo API key (DO THIS FIRST)
Devanshu just purchased Apollo Basic Monthly ($59/mo) on **devanshichi9@gmail.com**.

Steps:
1. Go to app.apollo.io → log in with devanshichi9@gmail.com
2. Settings → Integrations → API → copy API key
3. Open `backend/.env` → update `APOLLO_API_KEY=<new key>`
4. Restart backend: `uvicorn app.main:app --reload`
5. Test:
```bash
cd backend
python -c "
import asyncio, httpx, os
from dotenv import load_dotenv
load_dotenv(override=True)
key = os.getenv('APOLLO_API_KEY')
print('Key:', key[:8] if key else 'MISSING')

async def test():
    async with httpx.AsyncClient(timeout=30) as c:
        r = await c.post(
            'https://api.apollo.io/api/v1/mixed_people/search',
            headers={'X-Api-Key': key, 'Content-Type': 'application/json'},
            json={'q_organization_name': 'Stripe', 'page': 1, 'per_page': 5}
        )
        print('Status:', r.status_code)
        print(r.text[:500])

asyncio.run(test())
"
```

### 2. Full end-to-end test after Apollo is working
- Create a new outreach in the wizard
- Company: "Stripe", Location: "San Francisco, CA"
- Select a template, draft email, search contacts
- Verify contacts come back with emails
- Test copy buttons in Send step

### 3. Location filtering (already coded — verify it works)
`_normalize_location()` in apollo_service.py converts "San Francisco, CA" → Apollo `person_locations` filter. Verify this actually narrows results when tested.

### 4. Three users need to be set up
- Devanshu: user ID `193871f2-996c-49fa-9222-402bc3621cb0`, already seeded
- Friend 1 (SWE): needs account + profile + templates seeded
- Friend 2 (PM): needs account + profile + templates seeded
Each is fully isolated — own profile, own templates, own outreach history.

### 5. Deploy to Railway (not done yet)
Backend is local only right now. When ready to deploy:
- Set all env vars in Railway dashboard (same as .env)
- Update CORS_ORIGINS to include the frontend domain
- Frontend needs VITE_API_URL env var pointing to Railway URL

---

## HOW TO RUN LOCALLY

```bash
# Backend
cd /Users/devanshu/Desktop/Job-Outreach/backend
source venv/bin/activate   # or whatever venv name
uvicorn app.main:app --reload

# Frontend (separate terminal)
cd /Users/devanshu/Desktop/Job-Outreach/frontend
npm run dev
```

Frontend: http://localhost:5173
Backend: http://localhost:8000
API docs: http://localhost:8000/docs

---

## TONE FOR THIS PROJECT

Talk to Devanshu like a senior engineer who is also a friend. Direct. No fluff. When something is broken, say what it is and give the exact fix. Don't ask him to "consider" things — tell him what to do. Keep answers tight. He moves fast.

When he sends a screenshot of an error, read it immediately and tell him exactly what went wrong and the exact line to fix. Don't make him dig.

When he asks "is this working?" — look at the screenshot and give him a yes/no first, then explain.

He is a strong engineer. Don't over-explain basics. Treat him like a peer.
