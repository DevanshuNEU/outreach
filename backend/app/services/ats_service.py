import asyncio
import httpx

# Supported ATS types and their public API patterns
ATS_CONFIGS = {
    "greenhouse": {
        "url_template": "https://api.greenhouse.io/v1/boards/{slug}/jobs?content=true",
        "method": "GET",
    },
    "lever": {
        "url_template": "https://api.lever.co/v0/postings/{slug}",
        "method": "GET",
    },
    "ashby": {
        "url_template": "https://api.ashbyhq.com/posting-api/job-board/{slug}",
        "method": "GET",
    },
}


def _normalize_greenhouse_job(job: dict, company_name: str) -> dict:
    """Normalize a Greenhouse job to our standard format."""
    loc = job.get("location", {})
    location_name = loc.get("name", "") if isinstance(loc, dict) else str(loc)

    return {
        "title": job.get("title", ""),
        "job_id": str(job.get("id", "")),
        "location": location_name,
        "url": job.get("absolute_url", ""),
        "department": (
            (job.get("departments", [{}]) or [{}])[0].get("name", "")
            if job.get("departments")
            else ""
        ),
        "updated_at": job.get("updated_at", ""),
        "company_name": company_name,
    }


def _normalize_lever_job(job: dict, company_name: str) -> dict:
    """Normalize a Lever job to our standard format."""
    categories = job.get("categories", {})
    return {
        "title": job.get("text", ""),
        "job_id": str(job.get("id", "")),
        "location": (
            categories.get("location", "") if isinstance(categories, dict) else ""
        ),
        "url": job.get("hostedUrl", ""),
        "department": (
            categories.get("department", "") if isinstance(categories, dict) else ""
        ),
        "updated_at": "",
        "company_name": company_name,
    }


def _normalize_ashby_job(job: dict, company_name: str) -> dict:
    """Normalize an Ashby job to our standard format."""
    return {
        "title": job.get("title", ""),
        "job_id": str(job.get("id", "")),
        "location": job.get("location", ""),
        "url": job.get("jobUrl", job.get("applyUrl", "")),
        "department": job.get("departmentName", ""),
        "updated_at": job.get("publishedAt", ""),
        "company_name": company_name,
    }


NORMALIZERS = {
    "greenhouse": _normalize_greenhouse_job,
    "lever": _normalize_lever_job,
    "ashby": _normalize_ashby_job,
}

# Keywords to filter for SWE/AI/infra roles
SWE_TITLE_KEYWORDS = [
    "software", "engineer", "developer", "swe", "full stack", "fullstack",
    "full-stack", "backend", "back-end", "front-end", "frontend",
    "platform", "infrastructure", "infra", "devops", "sre",
    "machine learning", "ml ", "ai ", "data scientist", "data engineer",
    "systems engineer", "distributed", "cloud",
]

# Keywords to exclude (non-engineering roles)
EXCLUDE_TITLE_KEYWORDS = [
    "marketing", "sales", "account executive", "customer success",
    "recruiter", "talent", "hr ", "human resources", "legal", "counsel",
    "finance", "accounting", "content", "copywriter", "designer",
    "product manager", "program manager",
]


def _is_relevant_title(title: str) -> bool:
    """Check if a job title is relevant (SWE/AI/infra)."""
    title_lower = title.lower()
    has_match = any(kw in title_lower for kw in SWE_TITLE_KEYWORDS)
    is_excluded = any(kw in title_lower for kw in EXCLUDE_TITLE_KEYWORDS)
    return has_match and not is_excluded


async def fetch_ats_jobs(
    ats_type: str,
    slug: str,
    company_name: str,
    filter_engineering: bool = True,
    keywords: list[str] | None = None,
) -> list[dict]:
    """Fetch jobs from a company's public ATS API.

    Args:
        ats_type: One of 'greenhouse', 'lever', 'ashby'
        slug: The company's slug/board ID on the ATS
        company_name: Human-readable company name
        filter_engineering: Only return engineering-relevant roles
        keywords: Additional keyword filters
    """
    config = ATS_CONFIGS.get(ats_type)
    if not config:
        return []

    url = config["url_template"].format(slug=slug)

    async with httpx.AsyncClient(timeout=30) as client:
        try:
            if config["method"] == "GET":
                r = await client.get(url)
            else:
                r = await client.post(url)
            if r.status_code != 200:
                print(f"[ATS] {ats_type}/{slug} returned {r.status_code}")
                return []
            data = r.json()
        except Exception as e:
            print(f"[ATS] Error fetching {ats_type}/{slug}: {e}")
            return []

    # Extract jobs list from response
    if ats_type == "greenhouse":
        jobs_raw = data.get("jobs", []) if isinstance(data, dict) else []
    elif ats_type == "lever":
        jobs_raw = data if isinstance(data, list) else []
    elif ats_type == "ashby":
        jobs_raw = data.get("jobs", []) if isinstance(data, dict) else []
    else:
        jobs_raw = []

    # Normalize
    normalizer = NORMALIZERS[ats_type]
    jobs = [normalizer(j, company_name) for j in jobs_raw]

    if filter_engineering:
        jobs = [j for j in jobs if _is_relevant_title(j["title"])]

    if keywords:
        kw_lower = [k.lower() for k in keywords]
        jobs = [
            j for j in jobs if any(kw in j["title"].lower() for kw in kw_lower)
        ]

    return jobs


async def scan_all_targets(
    targets: list[dict], keywords: list[str] | None = None
) -> list[dict]:
    """Scan all target companies for new jobs.

    Args:
        targets: List of dicts with keys: ats_type, ats_slug, company_name
        keywords: Optional keyword filter

    Returns:
        List of normalized job dicts with target info
    """

    async def _scan_one(target: dict) -> list[dict]:
        jobs = await fetch_ats_jobs(
            ats_type=target["ats_type"],
            slug=target["ats_slug"],
            company_name=target.get("company_name", "Unknown"),
            filter_engineering=True,
            keywords=keywords,
        )
        for j in jobs:
            j["target_id"] = target.get("id", "")
        return jobs

    results = await asyncio.gather(
        *[_scan_one(t) for t in targets], return_exceptions=True
    )

    all_jobs = []
    for r in results:
        if isinstance(r, list):
            all_jobs.extend(r)

    return all_jobs
