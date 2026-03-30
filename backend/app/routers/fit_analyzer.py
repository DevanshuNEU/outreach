import httpx
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from app.auth.deps import get_current_user
from app.database import get_db
from app.config import settings
import anthropic
from bs4 import BeautifulSoup

router = APIRouter(prefix="/api", tags=["fit-analyzer"])


class FitRequest(BaseModel):
    job_url: str | None = None
    job_description: str | None = None  # fallback if URL scraping fails


class FitResult(BaseModel):
    fit_score: int           # 1-10
    verdict: str             # "Strong Yes" | "Yes" | "Borderline" | "No"
    verdict_reason: str      # 1 sentence why
    strengths: list[str]     # 3-5 bullets — specific matches
    gaps: list[str]          # 1-3 bullets — honest gaps
    talking_points: list[str]  # 2-3 bullets — what to lead with in cold email
    company_name: str | None
    job_title: str | None
    extracted_jd: str        # raw JD text we scraped/used


async def _fetch_jd_text(url: str) -> str:
    """Fetch a job posting URL and extract meaningful text."""
    headers = {
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }
    async with httpx.AsyncClient(timeout=15, follow_redirects=True) as client:
        resp = await client.get(url, headers=headers)
        if resp.status_code != 200:
            raise HTTPException(400, f"Could not fetch URL (status {resp.status_code}). Paste the JD text directly instead.")

    soup = BeautifulSoup(resp.text, "html.parser")

    # Remove noise
    for tag in soup(["script", "style", "nav", "footer", "header", "aside", "meta"]):
        tag.decompose()

    text = soup.get_text(separator="\n", strip=True)

    # Trim to ~4000 chars — enough for any JD, avoids token blowout
    if len(text) > 4000:
        text = text[:4000]

    return text


FIT_SYSTEM_PROMPT = """You are a brutally honest job-fit advisor for a strong software engineer.
Your job is to analyze a job description against a candidate's background and give a clear, specific verdict.

Be honest. If there are real gaps, say so. Don't fluff. Don't say "you'd be a great fit!" when you mean "maybe."

Output STRICT JSON only. No commentary outside the JSON.

JSON format:
{
  "fit_score": <int 1-10>,
  "verdict": <"Strong Yes" | "Yes" | "Borderline" | "No">,
  "verdict_reason": "<1 sentence — the single most important reason for this verdict>",
  "strengths": ["<specific match 1>", "<specific match 2>", ...],
  "gaps": ["<honest gap 1>", ...],
  "talking_points": ["<what to lead with in cold email 1>", ...],
  "company_name": "<extracted company name or null>",
  "job_title": "<extracted job title or null>"
}

Scoring guide:
8-10 = Strong Yes — background directly maps to 80%+ of requirements, visa-friendly company likely
6-7 = Yes — solid match with minor gaps, worth reaching out
4-5 = Borderline — some fit but notable gaps or unlikely to sponsor
1-3 = No — wrong stack, wrong level, or clear mismatch"""


@router.post("/analyze-fit", response_model=FitResult)
async def analyze_fit(
    req: FitRequest,
    current_user: dict = Depends(get_current_user),
):
    db = get_db()

    # Get user profile
    profile_res = db.table("profiles").select("*").eq("user_id", current_user["id"]).execute()
    if not profile_res.data:
        raise HTTPException(404, "Profile not found. Set up your profile first.")
    profile = profile_res.data[0]

    # Get JD text
    jd_text = ""
    if req.job_url:
        try:
            jd_text = await _fetch_jd_text(req.job_url)
        except HTTPException:
            raise
        except Exception as e:
            if req.job_description:
                jd_text = req.job_description
            else:
                raise HTTPException(400, f"Failed to fetch URL: {str(e)}. Paste the JD text directly.")
    elif req.job_description:
        jd_text = req.job_description
    else:
        raise HTTPException(400, "Provide either job_url or job_description")

    if not jd_text.strip():
        raise HTTPException(400, "Could not extract text from this URL. Paste the JD directly.")

    # Build candidate summary
    background = profile.get("background", "")
    projects = profile.get("projects", [])
    projects_text = ""
    for p in (projects or []):
        if isinstance(p, dict):
            projects_text += f"- {p.get('name', '')}: {p.get('description', '')} ({p.get('metrics', '')})\n"

    user_msg = f"""JOB POSTING:
{jd_text}

---
CANDIDATE BACKGROUND:
{background}

PROJECTS:
{projects_text}

Analyze fit and return JSON."""

    import json

    try:
        client = anthropic.Anthropic(api_key=settings.anthropic_api_key)
        response = client.messages.create(
            model="claude-haiku-4-5-20251001",
            max_tokens=1500,
            system=FIT_SYSTEM_PROMPT,
            messages=[{"role": "user", "content": user_msg}],
        )
    except Exception as e:
        raise HTTPException(500, f"AI service error: {str(e)}")

    raw = response.content[0].text.strip()

    # Parse JSON — handle code blocks if model wraps it
    if raw.startswith("```"):
        raw = raw.split("```")[1]
        if raw.startswith("json"):
            raw = raw[4:]
    raw = raw.strip()

    try:
        data = json.loads(raw)
    except Exception:
        raise HTTPException(500, f"Failed to parse AI response: {raw[:200]}")

    # Log usage
    db.table("api_usage").insert({
        "user_id": current_user["id"],
        "service": "anthropic",
        "endpoint": "fit_analysis",
        "tokens_in": response.usage.input_tokens,
        "tokens_out": response.usage.output_tokens,
        "estimated_cost_cents": round(
            response.usage.input_tokens * 0.0001 + response.usage.output_tokens * 0.0005, 4
        ),
    }).execute()

    return FitResult(
        fit_score=data.get("fit_score", 5),
        verdict=data.get("verdict", "Borderline"),
        verdict_reason=data.get("verdict_reason", ""),
        strengths=data.get("strengths", []),
        gaps=data.get("gaps", []),
        talking_points=data.get("talking_points", []),
        company_name=data.get("company_name"),
        job_title=data.get("job_title"),
        extracted_jd=jd_text,
    )
