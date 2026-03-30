import uuid
import json
import anthropic
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from app.database import get_db
from app.auth.deps import get_current_user
from app.models.schemas import TemplateCreate, TemplateUpdate, TemplateOut
from app.config import settings

router = APIRouter(prefix="/api/templates", tags=["templates"])

ROLE_TYPES = [
    ("swe",       "Software Engineer",        "#3b82f6"),
    ("ai-ml",     "AI/ML Engineer",           "#8b5cf6"),
    ("fullstack", "Full Stack Engineer",      "#10b981"),
    ("backend",   "Backend Engineer",         "#64748b"),
    ("cloud",     "Cloud / DevOps / SRE",     "#06b6d4"),
    ("fde",       "Forward-Deployed Engineer","#f59e0b"),
    ("rag",       "RAG Engineer",             "#d946ef"),
    ("data",      "Data Engineer",            "#ec4899"),
]

GENERATE_SYSTEM = """You generate cold email role templates for a job seeker.
Given their background and projects, output 8 role-specific prompt additions in JSON.

Each template has:
- slug: short identifier
- title: role display name
- color: hex color (provided)
- tagline: 1 punchy sentence, 10 words max, about their strongest angle for this role
- sort_order: integer 0-7
- role_prompt_addition: detailed prompt fragment (200-400 words) that tells the email AI:
  * The role's PSYCHOLOGICAL FRAME (how to position this candidate for this specific role)
  * SUBJECT LINE options (2-3 options, specific to their background)
  * HOOK instructions (what company-specific angle to research)
  * CONNECTION story (which of their projects/background to lead with for this role)
  * BULLET options (3-5 specific bullets using their real metrics)
  * CTA suggestion
  * DON'T list (3-4 things to avoid for this role)
- example_email: a sample cold email using their actual background (150-180 words total incl subject)

Use ONLY the candidate's actual projects and metrics. Do not invent numbers or stories.
Every template must feel like it was written for THIS person, not a generic template.

Output strict JSON array with 8 objects. No commentary outside the JSON."""


class SuggestTemplateRequest(BaseModel):
    company_name: str
    job_description: str

    class Config:
        extra = "allow"


@router.post("/suggest")
def suggest_template(
    req: SuggestTemplateRequest,
    current_user: dict = Depends(get_current_user),
):
    """Analyze a JD and return the best matching template for this user."""
    db = get_db()
    templates_res = (
        db.table("role_templates")
        .select("id,slug,title")
        .eq("user_id", current_user["id"])
        .execute()
    )
    if not templates_res.data:
        raise HTTPException(404, "No templates found — complete onboarding first")

    slugs = [t["slug"] for t in templates_res.data]
    slug_descriptions = {
        "rag": "retrieval, embeddings, vector search, RAG pipelines",
        "ai-ml": "ML engineering, model training, AI products, LLM applications",
        "context": "context engineering, prompt engineering, AI grounding",
        "cloud": "DevOps, SRE, platform engineering, Kubernetes, Terraform, infrastructure",
        "fde": "forward-deployed, solutions engineering, customer-facing technical roles",
        "backend": "APIs, distributed systems, databases, backend services, microservices, payments",
        "fullstack": "frontend + backend, product engineering, full-stack web",
        "swe": "general software engineering, doesn't fit cleanly into above",
    }
    slug_list = "\n".join(
        f"- {s}: {slug_descriptions.get(s, s)}" for s in slugs
    )

    client = anthropic.Anthropic(api_key=settings.anthropic_api_key)
    response = client.messages.create(
        model="claude-haiku-4-5-20251001",
        max_tokens=15,
        system=f"Pick the single best template slug for this job description.\n\nAvailable slugs:\n{slug_list}\n\nReturn ONLY the slug. One word. Nothing else.",
        messages=[{"role": "user", "content": f"Company: {req.company_name}\n\nJob Description:\n{req.job_description[:2000]}"}],
    )

    suggested_slug = response.content[0].text.strip().lower().split()[0]
    match = next((t for t in templates_res.data if t["slug"] == suggested_slug), templates_res.data[0])
    return {"template_id": match["id"], "slug": match["slug"], "title": match["title"]}


@router.get("", response_model=list[TemplateOut])
def list_templates(current_user: dict = Depends(get_current_user)):
    db = get_db()
    result = (
        db.table("role_templates")
        .select("*")
        .eq("user_id", current_user["id"])
        .order("sort_order")
        .execute()
    )
    return result.data


@router.post("", response_model=TemplateOut)
def create_template(req: TemplateCreate, current_user: dict = Depends(get_current_user)):
    db = get_db()
    data = req.model_dump()
    data["id"] = str(uuid.uuid4())
    data["user_id"] = current_user["id"]
    result = db.table("role_templates").insert(data).execute()
    return result.data[0]


@router.put("/{template_id}", response_model=TemplateOut)
def update_template(
    template_id: str,
    req: TemplateUpdate,
    current_user: dict = Depends(get_current_user),
):
    db = get_db()
    updates = req.model_dump(exclude_none=True)
    if not updates:
        raise HTTPException(400, "No fields to update")
    result = (
        db.table("role_templates")
        .update(updates)
        .eq("id", template_id)
        .eq("user_id", current_user["id"])
        .execute()
    )
    if not result.data:
        raise HTTPException(404, "Template not found")
    return result.data[0]


@router.delete("/{template_id}")
def delete_template(template_id: str, current_user: dict = Depends(get_current_user)):
    db = get_db()
    db.table("role_templates").delete().eq("id", template_id).eq("user_id", current_user["id"]).execute()
    return {"ok": True}


@router.post("/generate", response_model=list[TemplateOut])
async def generate_templates(current_user: dict = Depends(get_current_user)):
    """
    Auto-generates 8 role templates from the user's profile using Claude.
    Call this once after a new user fills in their profile.
    Deletes existing templates for this user first.
    """
    db = get_db()

    # Get profile
    profile_res = db.table("profiles").select("*").eq("user_id", current_user["id"]).execute()
    if not profile_res.data:
        raise HTTPException(404, "Fill in your profile first before generating templates.")
    profile = profile_res.data[0]

    background = profile.get("background", "")
    projects = profile.get("projects", [])
    if not background.strip():
        raise HTTPException(400, "Your profile background is empty. Add your background first.")

    # Build project summary
    projects_text = ""
    for p in (projects or []):
        if isinstance(p, dict):
            projects_text += f"- {p.get('name')}: {p.get('description', '')} | Metrics: {p.get('metrics', 'none')}\n"

    user_msg = f"""Generate 8 role templates for this candidate.

BACKGROUND:
{background}

PROJECTS:
{projects_text}

ROLE TYPES TO GENERATE (use these exact slugs, titles, colors, and sort_orders):
{json.dumps([{"slug": s, "title": t, "color": c, "sort_order": i} for i, (s, t, c) in enumerate(ROLE_TYPES)], indent=2)}

Output a JSON array of 8 template objects."""

    client = anthropic.Anthropic(api_key=settings.anthropic_api_key)
    response = client.messages.create(
        model="claude-haiku-4-5-20251001",
        max_tokens=4000,
        system=GENERATE_SYSTEM,
        messages=[{"role": "user", "content": user_msg}],
    )

    raw = response.content[0].text.strip()
    if raw.startswith("```"):
        raw = raw.split("```")[1]
        if raw.startswith("json"):
            raw = raw[4:]
    raw = raw.strip()

    try:
        templates_data = json.loads(raw)
    except Exception:
        raise HTTPException(500, "Failed to parse AI-generated templates. Try again.")

    # Delete existing templates for this user
    db.table("role_templates").delete().eq("user_id", current_user["id"]).execute()

    # Insert new ones
    saved = []
    for t in templates_data:
        t["id"] = str(uuid.uuid4())
        t["user_id"] = current_user["id"]
        t.setdefault("system_prompt", "")
        result = db.table("role_templates").insert(t).execute()
        if result.data:
            saved.append(result.data[0])

    # Log usage
    db.table("api_usage").insert({
        "user_id": current_user["id"],
        "service": "anthropic",
        "endpoint": "generate_templates",
        "tokens_in": response.usage.input_tokens,
        "tokens_out": response.usage.output_tokens,
        "estimated_cost_cents": round(
            response.usage.input_tokens * 0.0001 + response.usage.output_tokens * 0.0005, 4
        ),
    }).execute()

    return saved
