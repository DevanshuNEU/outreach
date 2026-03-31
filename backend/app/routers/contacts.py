import uuid
from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from app.database import get_db
from app.auth.deps import get_current_user
from app.services.apollo_service import search_company, find_contacts, get_cached_contacts, enrich_person
from app.models.schemas import ContactOut

router = APIRouter(prefix="/api", tags=["contacts"])


class ManualContactCreate(BaseModel):
    company_id: str
    first_name: str
    last_name: str
    title: str | None = None
    email: str
    linkedin_url: str | None = None


class EnrichContactRequest(BaseModel):
    company_id: str
    first_name: str
    last_name: str
    domain: str | None = None
    organization_name: str | None = None
    title: str | None = None
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


@router.post("/contacts/enrich", response_model=ContactOut)
async def enrich_contact(
    req: EnrichContactRequest,
    current_user: dict = Depends(get_current_user),
):
    """
    Find someone's verified email via Apollo enrichment.
    User provides name + company domain (from LinkedIn).
    Costs 1 Apollo credit. Way more reliable than search for small companies.
    """
    result = await enrich_person(
        first_name=req.first_name,
        last_name=req.last_name,
        domain=req.domain,
        organization_name=req.organization_name,
        user_id=current_user["id"],
    )
    if not result:
        raise HTTPException(404, "Could not find a verified email for this person. Try checking their LinkedIn or company website directly.")

    # Save to DB
    db = get_db()
    data = {
        "id": str(uuid.uuid4()),
        "company_id": req.company_id,
        "first_name": result["first_name"],
        "last_name": result["last_name"],
        "title": req.title or result.get("title", ""),
        "email": result["email"],
        "email_status": result["email_status"],
        "linkedin_url": req.linkedin_url or result.get("linkedin_url", ""),
        "seniority": result.get("seniority"),
        "apollo_person_id": result.get("apollo_person_id"),
    }

    # Check for existing contact with same apollo_person_id
    if result.get("apollo_person_id"):
        existing = db.table("contacts").select("*").eq("apollo_person_id", result["apollo_person_id"]).execute()
        if existing.data:
            return existing.data[0]

    saved = db.table("contacts").insert(data).execute()
    return saved.data[0]


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
