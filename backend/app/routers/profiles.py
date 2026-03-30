from fastapi import APIRouter, Depends, HTTPException
from app.database import get_db
from app.auth.deps import get_current_user
from app.models.schemas import ProfileUpdate, ProfileOut

router = APIRouter(prefix="/api/profile", tags=["profile"])


@router.get("", response_model=ProfileOut)
def get_profile(current_user: dict = Depends(get_current_user)):
    db = get_db()
    result = db.table("profiles").select("*").eq("user_id", current_user["id"]).execute()
    if not result.data:
        raise HTTPException(404, "Profile not found")
    return result.data[0]


@router.put("", response_model=ProfileOut)
def update_profile(req: ProfileUpdate, current_user: dict = Depends(get_current_user)):
    db = get_db()
    updates = req.model_dump(exclude_none=True)
    if "projects" in updates:
        updates["projects"] = [p if isinstance(p, dict) else p.model_dump() for p in updates["projects"]]

    result = (
        db.table("profiles")
        .update(updates)
        .eq("user_id", current_user["id"])
        .execute()
    )
    if not result.data:
        raise HTTPException(404, "Profile not found")
    return result.data[0]
