import uuid
from fastapi import APIRouter, Depends, HTTPException, Query
from app.database import get_db
from app.auth.deps import get_current_user
from app.models.schemas import ApplicationCreate, ApplicationUpdate, ApplicationOut

router = APIRouter(prefix="/api/applications", tags=["applications"])


@router.get("", response_model=list[ApplicationOut])
def list_applications(
    status: str | None = Query(None),
    current_user: dict = Depends(get_current_user),
):
    db = get_db()
    query = (
        db.table("applications")
        .select("*")
        .eq("user_id", current_user["id"])
        .order("created_at", desc=True)
    )
    if status:
        query = query.eq("status", status)
    result = query.execute()
    apps = result.data

    if apps:
        app_ids = [a["id"] for a in apps]
        outreach_res = (
            db.table("outreach")
            .select("application_id")
            .in_("application_id", app_ids)
            .execute()
        )
        counts: dict[str, int] = {}
        for row in outreach_res.data or []:
            aid = row["application_id"]
            counts[aid] = counts.get(aid, 0) + 1
        for a in apps:
            a["contact_count"] = counts.get(a["id"], 0)

    return apps


@router.post("", response_model=ApplicationOut)
def create_application(req: ApplicationCreate, current_user: dict = Depends(get_current_user)):
    db = get_db()
    data = req.model_dump()
    data["id"] = str(uuid.uuid4())
    data["user_id"] = current_user["id"]
    data["email_status"] = "draft"
    data["status"] = "drafting"
    result = db.table("applications").insert(data).execute()
    return result.data[0]


@router.get("/{app_id}", response_model=ApplicationOut)
def get_application(app_id: str, current_user: dict = Depends(get_current_user)):
    db = get_db()
    result = (
        db.table("applications")
        .select("*")
        .eq("id", app_id)
        .eq("user_id", current_user["id"])
        .execute()
    )
    if not result.data:
        raise HTTPException(404, "Application not found")
    return result.data[0]


@router.put("/{app_id}", response_model=ApplicationOut)
def update_application(
    app_id: str,
    req: ApplicationUpdate,
    current_user: dict = Depends(get_current_user),
):
    db = get_db()
    updates = req.model_dump(exclude_none=True)
    if not updates:
        raise HTTPException(400, "No fields to update")
    result = (
        db.table("applications")
        .update(updates)
        .eq("id", app_id)
        .eq("user_id", current_user["id"])
        .execute()
    )
    if not result.data:
        raise HTTPException(404, "Application not found")
    return result.data[0]


@router.delete("/{app_id}")
def delete_application(app_id: str, current_user: dict = Depends(get_current_user)):
    db = get_db()
    db.table("applications").delete().eq("id", app_id).eq("user_id", current_user["id"]).execute()
    return {"ok": True}
