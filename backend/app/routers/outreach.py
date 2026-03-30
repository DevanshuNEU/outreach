import uuid
from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException, Query
from app.database import get_db
from app.auth.deps import get_current_user
from app.models.schemas import OutreachCreate, OutreachUpdate, OutreachOut

router = APIRouter(prefix="/api/outreach", tags=["outreach"])


@router.get("", response_model=list[OutreachOut])
def list_outreach(
    application_id: str | None = Query(None),
    current_user: dict = Depends(get_current_user),
):
    db = get_db()
    query = (
        db.table("outreach")
        .select("*, contacts(*)")
        .eq("user_id", current_user["id"])
        .order("created_at", desc=True)
    )
    if application_id:
        query = query.eq("application_id", application_id)
    result = query.execute()

    out = []
    for row in result.data:
        contact_data = row.pop("contacts", None)
        row["contact"] = contact_data
        out.append(row)
    return out


@router.post("", response_model=OutreachOut)
def create_outreach(req: OutreachCreate, current_user: dict = Depends(get_current_user)):
    db = get_db()
    # Get contact to build greeting
    contact = db.table("contacts").select("first_name").eq("id", req.contact_id).execute()
    greeting = f"Hey {contact.data[0]['first_name']}," if contact.data else "Hey,"

    data = {
        "id": str(uuid.uuid4()),
        "application_id": req.application_id,
        "contact_id": req.contact_id,
        "user_id": current_user["id"],
        "personalized_greeting": greeting,
        "replied": False,
    }
    result = db.table("outreach").insert(data).execute()
    return result.data[0]


@router.delete("")
def delete_outreach_by_application(
    application_id: str = Query(...),
    current_user: dict = Depends(get_current_user),
):
    db = get_db()
    # Verify ownership via the applications table before deleting
    app_check = (
        db.table("applications")
        .select("id")
        .eq("id", application_id)
        .eq("user_id", current_user["id"])
        .execute()
    )
    if not app_check.data:
        raise HTTPException(403, "Not your application")
    db.table("outreach").delete().eq("application_id", application_id).execute()
    return {"ok": True}


@router.put("/{outreach_id}", response_model=OutreachOut)
def update_outreach(
    outreach_id: str,
    req: OutreachUpdate,
    current_user: dict = Depends(get_current_user),
):
    db = get_db()
    updates = req.model_dump(exclude_none=True)
    if "replied" in updates and updates["replied"] and not updates.get("reply_date"):
        updates["reply_date"] = datetime.now(timezone.utc).isoformat()
    if not updates:
        raise HTTPException(400, "No fields to update")
    result = (
        db.table("outreach")
        .update(updates)
        .eq("id", outreach_id)
        .eq("user_id", current_user["id"])
        .execute()
    )
    if not result.data:
        raise HTTPException(404, "Outreach not found")
    return result.data[0]
