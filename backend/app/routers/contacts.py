import uuid
from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from app.database import get_db
from app.auth.deps import get_current_user
from app.services.apollo_service import search_company, find_contacts, get_cached_contacts
from app.models.schemas import ContactOut

router = APIRouter(prefix="/api", tags=["contacts"])


class ManualContactCreate(BaseModel):
    company_id: str
    first_name: str
    last_name: str
    title: str | None = None
    email: str
    linkedin_url: str | None = None


@router.post("/applications/{app_id}/find-contacts", response_model=list[ContactOut])
async def find_application_contacts(
    app_id: str,
    current_user: dict = Depends(get_current_user),
):
    db = get_db()

    # Get application + company
    app_result = (
        db.table("applications")
        .select("*, companies(*)")
        .eq("id", app_id)
        .eq("user_id", current_user["id"])
        .execute()
    )
    if not app_result.data:
        raise HTTPException(404, "Application not found")

    application = app_result.data[0]
    company = application.get("companies")
    if not company:
        raise HTTPException(404, "Company not found")

    company_id = company["id"]

    # Check cache first
    cached = await get_cached_contacts(company_id)
    if cached:
        return cached

    # Search Apollo for company org ID
    org = await search_company(company["name"], company.get("domain"))
    if not org:
        raise HTTPException(404, "Company not found on Apollo. Check your Apollo plan at app.apollo.io → Settings → Billing, then regenerate your API key.")

    org_id = org.get("id")
    emp_count = org.get("estimated_num_employees")

    # Update company with Apollo data
    db.table("companies").update({
        "apollo_org_id": org_id,
        "employee_count": emp_count,
        "industry": org.get("industry"),
        "website": org.get("website_url"),
    }).eq("id", company_id).execute()

    # Find contacts (pass company info so Apollo filters by city/region and we can cross-check results)
    contacts = await find_contacts(
        org_id,
        emp_count,
        company_id,
        current_user["id"],
        location=company.get("location"),
        company_name=company["name"],
        company_domain=company.get("domain"),
    )
    return contacts


@router.post("/contacts/manual", response_model=ContactOut)
def create_manual_contact(
    req: ManualContactCreate,
    current_user: dict = Depends(get_current_user),
):
    db = get_db()
    data = {
        "id": str(uuid.uuid4()),
        "company_id": req.company_id,
        "first_name": req.first_name,
        "last_name": req.last_name,
        "title": req.title,
        "email": req.email,
        "email_status": "manual",
        "linkedin_url": req.linkedin_url,
        "seniority": None,
        "apollo_person_id": None,
    }
    result = db.table("contacts").insert(data).execute()
    return result.data[0]


@router.get("/contacts", response_model=list[ContactOut])
def list_contacts(
    company_id: str = Query(...),
    current_user: dict = Depends(get_current_user),
):
    db = get_db()
    result = (
        db.table("contacts")
        .select("*")
        .eq("company_id", company_id)
        .execute()
    )
    return result.data
