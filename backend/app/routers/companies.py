import uuid
from fastapi import APIRouter, Depends
from app.database import get_db
from app.auth.deps import get_current_user
from app.models.schemas import CompanyCreate, CompanyOut

router = APIRouter(prefix="/api/companies", tags=["companies"])


@router.get("", response_model=list[CompanyOut])
def list_companies(current_user: dict = Depends(get_current_user)):
    db = get_db()
    result = db.table("companies").select("*").order("created_at", desc=True).execute()
    return result.data


@router.post("", response_model=CompanyOut)
def create_company(req: CompanyCreate, current_user: dict = Depends(get_current_user)):
    db = get_db()
    # Check if company already exists
    query = db.table("companies").select("*").eq("name", req.name)
    if req.location:
        query = query.eq("location", req.location)
    existing = query.execute()
    if existing.data:
        return existing.data[0]

    data = req.model_dump()
    data["id"] = str(uuid.uuid4())
    result = db.table("companies").insert(data).execute()
    return result.data[0]
