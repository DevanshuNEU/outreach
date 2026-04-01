import re
import asyncio
import httpx
from datetime import datetime

# Known thread IDs for recent months
HN_THREAD_IDS = {
    "2026-03": 47219668,
    "2026-02": 46857488,
    "2026-01": 46466074,
}

# Keywords that signal visa/OPT friendliness
VISA_KEYWORDS = [
    "visa", "sponsor", "opt", "stem opt", "h1b", "h-1b",
    "work authorization", "ead", "no sponsorship restriction",
]

# Keywords for SWE/AI/infra roles relevant to the user
ROLE_KEYWORDS = {
    "swe": [
        "software engineer", "software developer", "swe ", "full stack",
        "fullstack", "full-stack", "backend", "back-end", "frontend", "front-end",
    ],
    "ai-ml": [
        "machine learning", "ml engineer", "ai engineer", "artificial intelligence",
        "deep learning", "nlp", "llm", "generative ai", "data scientist",
    ],
    "infra": [
        "infrastructure", "platform engineer", "devops", "sre",
        "site reliability", "cloud engineer", "distributed systems", "systems engineer",
    ],
    "general": ["engineer", "developer", "programming"],
}


def _get_latest_thread_id() -> int:
    """Get the most recent Who is Hiring thread ID."""
    now = datetime.utcnow()
    key = f"{now.year}-{now.month:02d}"
    if key in HN_THREAD_IDS:
        return HN_THREAD_IDS[key]
    latest_key = sorted(HN_THREAD_IDS.keys())[-1]
    return HN_THREAD_IDS[latest_key]


def _parse_hn_comment(text: str) -> dict:
    """Parse an HN Who is Hiring comment into structured data."""
    if not text:
        return {}

    # Clean HTML
    clean = re.sub(r"<[^>]+>", "\n", text)
    clean = (
        clean.replace("&amp;", "&")
        .replace("&lt;", "<")
        .replace("&gt;", ">")
        .replace("&#x27;", "'")
        .replace("&quot;", '"')
        .replace("&#x2F;", "/")
    )

    lines = [l.strip() for l in clean.split("\n") if l.strip()]
    if not lines:
        return {}

    # HN comments sometimes span multiple lines before pipes.
    # Merge first few lines to find the pipe-separated header.
    # e.g. "Company Name (\nhttps://...\n) | Role | Location"
    header_candidate = lines[0]
    body_start = 1
    # If line 0 has no pipes, try merging with next lines (URLs often break the header)
    for j in range(1, min(5, len(lines))):
        if "|" in header_candidate:
            break
        header_candidate = header_candidate + " " + lines[j]
        body_start = j + 1

    # Clean up URL artifacts in header: "Company (\nhttps://...\n)" → "Company"
    header = re.sub(r'\s*\(\s*https?://[^\)]*\)\s*', ' ', header_candidate).strip()
    parts = [p.strip() for p in header.split("|")]

    # Detect if first part is a role title (not a company name)
    # Role titles usually contain words like Engineer, Developer, Lead, Senior, etc.
    role_indicators = {"engineer", "developer", "lead", "senior", "junior", "head of", "manager", "director", "architect", "scientist", "analyst", "designer"}
    first_lower = parts[0].lower() if parts else ""
    first_is_role = any(ri in first_lower for ri in role_indicators) and len(parts) >= 2

    if first_is_role and len(parts) >= 2:
        # Likely: "Role | Company | Location" or "Role\nCompany | Location"
        # Try to find company from the second part or from body
        company = parts[1] if len(parts) > 1 else ""
        role = parts[0]
        location = parts[2] if len(parts) > 2 else ""
    else:
        company = parts[0]
        role = parts[1] if len(parts) > 1 else ""
        location = parts[2] if len(parts) > 2 else ""

    result = {
        "company": company.strip(),
        "role": role.strip(),
        "location": location.strip(),
        "header": header,
        "body": "\n".join(lines[body_start:]) if len(lines) > body_start else "",
        "full_text": "\n".join(lines),
    }

    full_lower = result["full_text"].lower()

    result["remote"] = any(
        kw in full_lower
        for kw in ["remote", "fully remote", "remote ok", "remote friendly"]
    )

    result["visa_friendly"] = any(kw in full_lower for kw in VISA_KEYWORDS)

    # Extract URL if present
    urls = re.findall(r"https?://[^\s<>\"']+", text)
    result["apply_url"] = urls[0] if urls else ""

    # Detect role categories
    categories = []
    for cat, keywords in ROLE_KEYWORDS.items():
        if any(kw in full_lower for kw in keywords):
            categories.append(cat)
    result["categories"] = categories

    # Try to extract salary info
    salary_match = re.search(r"\$[\d,]+k?\s*[-\u2013]\s*\$?[\d,]+k?", result["full_text"])
    result["salary"] = salary_match.group(0) if salary_match else ""

    # Extract tech stack keywords
    tech_keywords = [
        "python", "typescript", "javascript", "react", "node", "go", "golang",
        "rust", "java", "kotlin", "swift", "c++", "ruby", "rails", "django",
        "fastapi", "flask", "aws", "gcp", "azure", "kubernetes", "docker",
        "terraform", "postgres", "redis", "kafka", "graphql", "grpc",
    ]
    result["tech_stack"] = [t for t in tech_keywords if t in full_lower]

    return result


async def fetch_hn_hiring(
    thread_id: int | None = None,
    keywords: list[str] | None = None,
    visa_only: bool = False,
    categories: list[str] | None = None,
    max_items: int = 200,
) -> list[dict]:
    """Fetch and parse HN Who is Hiring thread.

    Args:
        thread_id: Specific HN item ID. If None, uses latest known thread.
        keywords: Filter posts containing any of these keywords.
        visa_only: Only return visa-friendly posts.
        categories: Filter by role category (swe, ai-ml, infra).
        max_items: Max comments to fetch (HN API is per-item so this caps requests).
    """
    if thread_id is None:
        thread_id = _get_latest_thread_id()

    async with httpx.AsyncClient(timeout=30) as client:
        r = await client.get(
            f"https://hacker-news.firebaseio.com/v0/item/{thread_id}.json"
        )
        if r.status_code != 200:
            return []

        thread = r.json()
        kid_ids = thread.get("kids", [])[:max_items]

        # Fetch comments in batches of 20 for speed
        results = []
        batch_size = 20
        for i in range(0, len(kid_ids), batch_size):
            batch = kid_ids[i : i + batch_size]
            tasks = [
                client.get(
                    f"https://hacker-news.firebaseio.com/v0/item/{kid}.json"
                )
                for kid in batch
            ]

            responses = await asyncio.gather(*tasks, return_exceptions=True)

            for resp in responses:
                if isinstance(resp, Exception) or resp.status_code != 200:
                    continue
                data = resp.json()
                if not data or data.get("deleted") or data.get("dead"):
                    continue

                parsed = _parse_hn_comment(data.get("text", ""))
                if not parsed or not parsed.get("company"):
                    continue

                parsed["hn_id"] = data.get("id")
                parsed["hn_url"] = (
                    f"https://news.ycombinator.com/item?id={data.get('id')}"
                )
                parsed["posted_at"] = (
                    datetime.utcfromtimestamp(data.get("time", 0)).isoformat()
                    if data.get("time")
                    else ""
                )

                results.append(parsed)

        # Apply filters
        filtered = results

        if visa_only:
            filtered = [r for r in filtered if r.get("visa_friendly")]

        if categories:
            cat_set = set(c.lower() for c in categories)
            filtered = [
                r for r in filtered if set(r.get("categories", [])) & cat_set
            ]

        if keywords:
            kw_lower = [k.lower() for k in keywords]
            filtered = [
                r
                for r in filtered
                if any(kw in r.get("full_text", "").lower() for kw in kw_lower)
            ]

        return filtered
