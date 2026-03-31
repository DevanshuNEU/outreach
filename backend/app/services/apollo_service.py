import uuid
import httpx
from datetime import datetime, timezone
from app.config import settings
from app.database import get_db

APOLLO_BASE = "https://api.apollo.io"

# Apollo now requires the key in the X-Api-Key header, not the request body
def _apollo_headers() -> dict:
    return {
        "X-Api-Key": settings.apollo_api_key,
        "Content-Type": "application/json",
        "Cache-Control": "no-cache",
    }


SENIORITY_FILTERS = {
    # Startup <50: go straight to the top — CEO/CTO makes every hire.
    # Target 1-2 people max. No recruiters at this size.
    "startup": {
        "searches": [
            {"person_seniorities": ["owner", "founder", "c_suite"], "person_titles": ["CTO", "CEO", "Co-Founder", "VP Engineering", "Head of Engineering"]},
            {"person_seniorities": ["director", "manager"], "person_titles": ["Engineering", "Software", "Technology"]},
        ],
        "per_page": 3,
    },
    # Growth 50-500: Engineering Manager is the highest-ROI target.
    # They are literally judged on how fast they hire. Recruiter is secondary.
    "growth": {
        "searches": [
            {"person_seniorities": ["manager", "director"], "person_titles": ["Engineering Manager", "Director of Engineering", "Head of Engineering", "VP Engineering"]},
            {"person_titles": ["Technical Recruiter", "Engineering Recruiter", "Talent Acquisition"]},
        ],
        "per_page": 5,
    },
    # Midsize 500-5000: Hiring manager first, then technical recruiter.
    # Never spray — EM + 1 recruiter is the ceiling.
    "midsize": {
        "searches": [
            {"person_seniorities": ["manager", "director"], "person_titles": ["Engineering Manager", "Software Engineering Manager", "Director of Engineering"]},
            {"person_titles": ["Technical Recruiter", "University Recruiter", "Campus Recruiter", "Early Career Recruiter", "New Grad Recruiter"]},
        ],
        "per_page": 5,
    },
    # Enterprise 5000+: University/new grad recruiters own the OPT pipeline.
    # They know exactly what to do with F1/OPT candidates. Hit them + 1 EM.
    "enterprise": {
        "searches": [
            {"person_titles": ["University Recruiter", "Campus Recruiter", "Early Career Recruiter", "New Grad Recruiter", "University Programs"]},
            {"person_seniorities": ["manager", "director"], "person_titles": ["Engineering Manager", "Software Engineering Manager"]},
        ],
        "per_page": 5,
    },
}

# Email statuses we accept, in priority order
ACCEPTED_EMAIL_STATUSES = {"verified", "likely", "guessed"}


def _get_daily_apollo_credits_used(db) -> int:
    """Count Apollo credits used today (global, not per-user — credits are a shared account resource)."""
    today_start = datetime.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0).isoformat()
    result = (
        db.table("api_usage")
        .select("estimated_cost_cents")
        .eq("service", "apollo")
        .gte("created_at", today_start)
        .execute()
    )
    return sum(r.get("estimated_cost_cents", 0) or 0 for r in (result.data or []))


def _get_company_tier(employee_count: int | None) -> str:
    if employee_count is None or employee_count <= 20:
        return "startup"
    elif employee_count <= 500:
        return "growth"
    elif employee_count <= 5000:
        return "midsize"
    return "enterprise"


def _name_matches(query: str, candidate: str) -> bool:
    """
    Return True if the Apollo-returned company name is a reasonable match for what we searched.
    Guards against Apollo returning a totally unrelated company (e.g. searching 'Bobyard' and
    getting back 'Google').

    Rules (any one is enough to accept):
      1. Query is a substring of candidate name (case-insensitive)
      2. Candidate name is a substring of query
      3. Any non-trivial word in the query (len >= 3) appears in the candidate name
    """
    q = query.lower().strip()
    c = candidate.lower().strip()
    if q in c or c in q:
        return True
    # Word overlap — ignore tiny words like "the", "of", "inc"
    q_words = {w for w in q.split() if len(w) >= 3}
    c_words = {w for w in c.split() if len(w) >= 3}
    return bool(q_words & c_words)


async def search_company(company_name: str, domain: str | None = None) -> dict | None:
    async with httpx.AsyncClient(timeout=30) as client:
        # ── Layer 1: prefer domain search (unambiguous) ───────────────────────
        # If a domain is provided, use it — domain search is exact, never returns wrong company.
        # If no domain, try to derive one (bobyard → bobyard.com) and try both.
        candidates_to_try: list[dict] = []

        if domain:
            candidates_to_try.append({"q_organization_domains": domain})
        else:
            # Derive a likely domain from company name: strip spaces/special chars
            derived_domain = company_name.lower().strip()
            derived_domain = "".join(c for c in derived_domain if c.isalnum() or c == "-")
            derived_domain = derived_domain + ".com"
            # Try domain first (most precise), fall back to name search
            candidates_to_try.append({"q_organization_domains": derived_domain})
            candidates_to_try.append({"q_organization_name": company_name})

        orgs = []
        for search_body in candidates_to_try:
            body = {"page": 1, "per_page": 5, **search_body}
            resp = await client.post(
                f"{APOLLO_BASE}/api/v1/mixed_companies/search",
                headers=_apollo_headers(),
                json=body,
            )
            if resp.status_code != 200:
                print(f"[Apollo] company search failed {resp.status_code}: {resp.text[:300]}")
                continue

            data = resp.json()
            found = data.get("organizations", [])
            if found:
                orgs = found
                print(f"[Apollo] company search via {list(search_body.keys())[0]}: {len(found)} results")
                break

        if not orgs:
            print(f"[Apollo] no orgs found for: {company_name}")
            return None

        # ── Layer 2: validate name match ──────────────────────────────────────
        # Apollo sometimes returns a completely wrong company as the top result.
        # Scan up to the top 5 results and pick the first whose name actually
        # matches what we searched for.
        matched_org = None
        for org in orgs[:5]:
            org_name = org.get("name") or ""
            if _name_matches(company_name, org_name):
                matched_org = org
                break

        if not matched_org:
            returned_names = [o.get("name") for o in orgs[:5]]
            print(
                f"[Apollo] SAFETY BLOCK: searched '{company_name}' but Apollo returned "
                f"{returned_names} — none match. Refusing to use wrong org."
            )
            return None

        print(
            f"[Apollo] verified org: '{matched_org.get('name')}' "
            f"(id={matched_org.get('id')}, employees={matched_org.get('estimated_num_employees')})"
        )
        return matched_org


def _normalize_location(location: str | None) -> list[str]:
    """
    Convert a free-text location like 'San Francisco, CA' into Apollo-compatible
    person_locations strings. Apollo accepts city/state/country combos like
    'San Francisco, California, United States'.

    We try a few common variations so partial matches still hit.
    """
    if not location:
        return []

    loc = location.strip()

    # Common abbreviation expansions
    state_map = {
        "CA": "California", "NY": "New York", "TX": "Texas", "WA": "Washington",
        "MA": "Massachusetts", "IL": "Illinois", "CO": "Colorado", "GA": "Georgia",
        "FL": "Florida", "VA": "Virginia", "OR": "Oregon", "NC": "North Carolina",
        "AZ": "Arizona", "OH": "Ohio", "MN": "Minnesota", "MI": "Michigan",
        "NJ": "New Jersey", "PA": "Pennsylvania", "UT": "Utah", "MD": "Maryland",
    }

    # Try to detect "City, ST" pattern and expand to "City, State, United States"
    parts = [p.strip() for p in loc.split(",")]
    expanded_parts = []
    for p in parts:
        expanded_parts.append(state_map.get(p.upper(), p))

    # Build full location string with United States if not already there
    full_loc = ", ".join(expanded_parts)
    if "United States" not in full_loc and len(parts) <= 2:
        full_loc = full_loc + ", United States"

    # Return both the original and expanded versions for best coverage
    results = [full_loc]
    if full_loc != loc:
        results.append(loc)
    return results


async def _enrich_people_bulk(client: httpx.AsyncClient, person_ids: list[str]) -> list[dict]:
    """
    Use people/bulk_match to enrich up to 10 people at a time and reveal emails.
    Returns list of enriched person dicts.
    Costs 1 credit per person with a revealed email.
    """
    enriched = []
    # Process in batches of 10
    for i in range(0, len(person_ids), 10):
        batch = person_ids[i:i + 10]
        details = [{"id": pid, "reveal_personal_emails": True} for pid in batch]

        resp = await client.post(
            f"{APOLLO_BASE}/api/v1/people/bulk_match",
            headers=_apollo_headers(),
            json={"details": details},
        )
        if resp.status_code != 200:
            print(f"[Apollo] bulk_match failed {resp.status_code}: {resp.text[:200]}")
            continue

        matches = resp.json().get("matches", [])
        print(f"[Apollo] bulk_match batch {i//10 + 1}: {len(matches)} matches")
        enriched.extend(matches)

    return enriched


async def find_contacts(
    organization_id: str,
    employee_count: int | None,
    company_id: str,
    user_id: str,
    location: str | None = None,
    company_name: str | None = None,
    company_domain: str | None = None,
) -> list[dict]:
    db = get_db()
    tier = _get_company_tier(employee_count)
    config = SENIORITY_FILTERS[tier]
    seen_ids = set()
    candidate_ids = []  # Apollo person IDs to enrich

    # Build location filter once — reused across all searches
    person_locations = _normalize_location(location)
    if person_locations:
        print(f"[Apollo] filtering by person_locations={person_locations}")

    # Step 1: Search for people (FREE — no credits used)
    async with httpx.AsyncClient(timeout=30) as client:
        for search_filters in config["searches"]:
            body = {
                "organization_ids": [organization_id],
                "page": 1,
                "per_page": config["per_page"],
                **search_filters,
            }
            if person_locations:
                body["person_locations"] = person_locations

            resp = await client.post(
                f"{APOLLO_BASE}/api/v1/mixed_people/api_search",
                headers=_apollo_headers(),
                json=body,
            )

            if resp.status_code != 200:
                print(f"[Apollo] people search failed {resp.status_code}: {resp.text[:300]}")
                continue

            people = resp.json().get("people", [])
            print(f"[Apollo] search {search_filters} -> {len(people)} candidates")

            for person in people:
                pid = person.get("id")
                if pid and pid not in seen_ids:
                    seen_ids.add(pid)
                    # Only enrich people who have an email in Apollo's DB
                    if person.get("has_email"):
                        candidate_ids.append(pid)

        print(f"[Apollo] {len(candidate_ids)} candidates have emails — checking limits before enriching")

        # Cap per-search to avoid burning too many credits on one company
        if len(candidate_ids) > settings.apollo_max_contacts_per_search:
            print(f"[Apollo] capping from {len(candidate_ids)} → {settings.apollo_max_contacts_per_search} (max per search)")
            candidate_ids = candidate_ids[:settings.apollo_max_contacts_per_search]

        # Check daily credit limit (global across all users — Apollo credits are shared)
        daily_used = _get_daily_apollo_credits_used(db)
        remaining_today = settings.apollo_daily_credit_limit - daily_used
        if remaining_today <= 0:
            print(f"[Apollo] daily credit limit reached ({daily_used} used today). Returning empty.")
            return []
        if len(candidate_ids) > remaining_today:
            print(f"[Apollo] capping to daily budget: {len(candidate_ids)} → {remaining_today}")
            candidate_ids = candidate_ids[:remaining_today]

        print(f"[Apollo] enriching {len(candidate_ids)} candidates (costs credits)")

        # Step 2: Bulk enrich to reveal emails (costs 1 credit per person)
        enriched = await _enrich_people_bulk(client, candidate_ids)

    # Step 3: Filter contacts — usable email + org cross-check
    # Build domain allowlist for this company so we can catch wrong-org contacts.
    # e.g. searching Bobyard but getting @google.com emails → blocked.
    allowed_email_domains: set[str] = set()
    if company_domain:
        allowed_email_domains.add(company_domain.lower().lstrip("www.").strip())
    if company_name:
        # Derive likely domain from name as a secondary check
        derived = "".join(c for c in company_name.lower() if c.isalnum() or c == "-") + ".com"
        allowed_email_domains.add(derived)

    all_contacts = []
    for person in enriched:
        email = person.get("email")
        email_status = person.get("email_status", "")
        name = f"{person.get('first_name')} {person.get('last_name')}"

        if not email or email_status not in ACCEPTED_EMAIL_STATUSES:
            print(f"  skip {name}: email_status={email_status!r}")
            continue

        # ── Layer 3: org ID cross-check ───────────────────────────────────────
        # Apollo returns organization_id on enriched people. If it's present and
        # doesn't match what we searched for, this person works somewhere else.
        person_org_id = person.get("organization_id") or person.get("employment_history", [{}])[0].get("organization_id") if person.get("employment_history") else person.get("organization_id")
        if person_org_id and person_org_id != organization_id:
            print(f"  SAFETY SKIP {name}: person.organization_id={person_org_id!r} != searched {organization_id!r}")
            continue

        # ── Layer 3b: email domain cross-check ───────────────────────────────
        # If we have domain info and the email domain doesn't match at all, reject.
        if allowed_email_domains:
            email_domain = email.split("@")[-1].lower() if "@" in email else ""
            if email_domain and not any(email_domain.endswith(d) for d in allowed_email_domains):
                print(f"  SAFETY SKIP {name}: email {email!r} domain doesn't match company {allowed_email_domains}")
                continue

        all_contacts.append({
            "apollo_person_id": person.get("id"),
            "first_name": person.get("first_name", ""),
            "last_name": person.get("last_name", ""),
            "title": person.get("title", ""),
            "seniority": person.get("seniority", ""),
            "email": email,
            "email_status": email_status,
            "linkedin_url": person.get("linkedin_url", ""),
            "company_id": company_id,
        })

    print(f"[Apollo] total contacts with verified emails: {len(all_contacts)}")

    # Upsert contacts into DB (shared across users)
    saved = []
    for c in all_contacts:
        existing = (
            db.table("contacts")
            .select("*")
            .eq("apollo_person_id", c["apollo_person_id"])
            .execute()
        )
        if existing.data:
            saved.append(existing.data[0])
        else:
            c["id"] = str(uuid.uuid4())
            result = db.table("contacts").insert(c).execute()
            if result.data:
                saved.append(result.data[0])

    # Log API usage
    db.table("api_usage").insert({
        "user_id": user_id,
        "service": "apollo",
        "endpoint": "people_search",
        "estimated_cost_cents": len(saved),  # ~1 credit per contact
    }).execute()

    return saved


async def enrich_person(
    first_name: str,
    last_name: str,
    domain: str | None = None,
    organization_name: str | None = None,
    user_id: str | None = None,
) -> dict | None:
    """
    Given a person's name + company domain (from LinkedIn), hit Apollo's
    people/match to get their verified email. Costs 1 credit.
    Way more reliable than search for small companies.
    """
    body = {
        "first_name": first_name,
        "last_name": last_name,
        "reveal_personal_emails": True,
    }
    if domain:
        body["domain"] = domain
    elif organization_name:
        body["organization_name"] = organization_name

    async with httpx.AsyncClient(timeout=30) as client:
        resp = await client.post(
            f"{APOLLO_BASE}/api/v1/people/match",
            headers=_apollo_headers(),
            json=body,
        )

    if resp.status_code != 200:
        print(f"[Apollo] enrich failed {resp.status_code}: {resp.text[:200]}")
        return None

    person = resp.json().get("person")
    if not person:
        print(f"[Apollo] enrich: no match for {first_name} {last_name}")
        # Fallback: guess email from domain
        if domain:
            return {
                "apollo_person_id": None,
                "first_name": first_name,
                "last_name": last_name,
                "title": "",
                "seniority": "",
                "email": f"{first_name.lower()}@{domain}",
                "email_status": "guessed",
                "linkedin_url": "",
            }
        return None

    email = person.get("email")
    email_status = person.get("email_status", "")

    if not email or email_status not in ACCEPTED_EMAIL_STATUSES:
        print(f"[Apollo] enrich: {first_name} {last_name} has no usable email (status={email_status}), trying guess")
        # Fallback: guess firstname@domain for startups (reliable for <500 person companies)
        if domain:
            email = f"{first_name.lower()}@{domain}"
            email_status = "guessed"
        else:
            return None

    # Log usage
    if user_id:
        db = get_db()
        db.table("api_usage").insert({
            "user_id": user_id,
            "service": "apollo",
            "endpoint": "people_enrich",
            "estimated_cost_cents": 1,
        }).execute()

    return {
        "apollo_person_id": person.get("id"),
        "first_name": person.get("first_name", first_name),
        "last_name": person.get("last_name", last_name),
        "title": person.get("title", ""),
        "seniority": person.get("seniority", ""),
        "email": email,
        "email_status": email_status,
        "linkedin_url": person.get("linkedin_url", ""),
    }


async def get_cached_contacts(company_id: str) -> list[dict]:
    db = get_db()
    result = (
        db.table("contacts")
        .select("*")
        .eq("company_id", company_id)
        .execute()
    )
    return result.data
