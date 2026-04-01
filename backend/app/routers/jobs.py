import uuid
from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from app.database import get_db
from app.auth.deps import get_current_user
from app.services.hn_service import fetch_hn_hiring, HN_THREAD_IDS
from app.services.ats_service import fetch_ats_jobs, scan_all_targets

router = APIRouter(prefix="/api/jobs", tags=["jobs"])


# ── Schemas ──


class TargetCompanyCreate(BaseModel):
    company_name: str
    ats_type: str  # greenhouse, lever, ashby
    ats_slug: str
    keywords: str | None = None  # comma-separated


class TargetCompanyOut(BaseModel):
    id: str
    company_name: str
    ats_type: str
    ats_slug: str
    keywords: str | None = None
    created_at: str | None = None


# ── HN Who is Hiring ──


@router.get("/hn-hiring")
async def get_hn_hiring(
    thread_id: int | None = Query(None, description="Specific HN thread ID"),
    keywords: str | None = Query(
        None, description="Comma-separated keywords to filter"
    ),
    visa_only: bool = Query(False, description="Only show visa-friendly posts"),
    categories: str | None = Query(
        None, description="Comma-separated: swe,ai-ml,infra"
    ),
    max_items: int = Query(150, description="Max comments to fetch"),
    current_user: dict = Depends(get_current_user),
):
    """Fetch and parse the latest HN 'Who is Hiring?' thread."""
    kw_list = (
        [k.strip() for k in keywords.split(",") if k.strip()] if keywords else None
    )
    cat_list = (
        [c.strip() for c in categories.split(",") if c.strip()] if categories else None
    )

    results = await fetch_hn_hiring(
        thread_id=thread_id,
        keywords=kw_list,
        visa_only=visa_only,
        categories=cat_list,
        max_items=max_items,
    )

    return {
        "thread_id": thread_id or max(HN_THREAD_IDS.values()),
        "total": len(results),
        "jobs": results,
    }


# ── Target Companies (ATS Watcher) ──


@router.get("/targets", response_model=list[TargetCompanyOut])
def list_targets(current_user: dict = Depends(get_current_user)):
    """List all target companies being watched."""
    db = get_db()
    result = (
        db.table("target_companies")
        .select("*")
        .eq("user_id", current_user["id"])
        .order("created_at", desc=True)
        .execute()
    )
    return result.data or []


@router.post("/targets", response_model=TargetCompanyOut)
def add_target(req: TargetCompanyCreate, current_user: dict = Depends(get_current_user)):
    """Add a company to watch for new job postings."""
    db = get_db()

    if req.ats_type not in ("greenhouse", "lever", "ashby"):
        raise HTTPException(400, "ats_type must be greenhouse, lever, or ashby")

    data = req.model_dump()
    data["id"] = str(uuid.uuid4())
    data["user_id"] = current_user["id"]

    result = db.table("target_companies").insert(data).execute()
    return result.data[0]


@router.delete("/targets/{target_id}")
def remove_target(target_id: str, current_user: dict = Depends(get_current_user)):
    """Stop watching a company."""
    db = get_db()
    db.table("target_companies").delete().eq("id", target_id).eq(
        "user_id", current_user["id"]
    ).execute()
    return {"ok": True}


# ── ATS Job Scanner ──


@router.get("/scan/{target_id}")
async def scan_single_target(
    target_id: str,
    current_user: dict = Depends(get_current_user),
):
    """Scan a single target company for current job openings."""
    db = get_db()
    result = (
        db.table("target_companies")
        .select("*")
        .eq("id", target_id)
        .eq("user_id", current_user["id"])
        .execute()
    )
    if not result.data:
        raise HTTPException(404, "Target not found")

    target = result.data[0]
    kw_list = (
        [k.strip() for k in target["keywords"].split(",") if k.strip()]
        if target.get("keywords")
        else None
    )

    jobs = await fetch_ats_jobs(
        ats_type=target["ats_type"],
        slug=target["ats_slug"],
        company_name=target["company_name"],
        filter_engineering=True,
        keywords=kw_list,
    )

    return {
        "target": target,
        "total": len(jobs),
        "jobs": jobs,
    }


@router.post("/scan-all")
async def scan_all(
    keywords: str | None = Query(None, description="Additional keyword filter"),
    current_user: dict = Depends(get_current_user),
):
    """Scan ALL target companies for current job openings."""
    db = get_db()
    result = (
        db.table("target_companies")
        .select("*")
        .eq("user_id", current_user["id"])
        .execute()
    )
    targets = result.data or []
    if not targets:
        return {"total": 0, "jobs": [], "targets_scanned": 0}

    kw_list = (
        [k.strip() for k in keywords.split(",") if k.strip()] if keywords else None
    )

    jobs = await scan_all_targets(targets, keywords=kw_list)

    return {
        "targets_scanned": len(targets),
        "total": len(jobs),
        "jobs": jobs,
    }
