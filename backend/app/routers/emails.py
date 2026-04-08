from fastapi import APIRouter, Depends, HTTPException
from app.database import get_db
from app.auth.deps import get_current_user
from app.models.schemas import DraftEmailRequest
from app.services.email_service import draft_email
from app.services.apollo_service import search_company, _clean_company_name

router = APIRouter(prefix="/api/applications", tags=["emails"])


@router.post("/{app_id}/draft-email")
async def generate_draft(
    app_id: str,
    req: DraftEmailRequest,
    current_user: dict = Depends(get_current_user),
):
    db = get_db()

    # Get application
    app_result = (
        db.table("applications")
        .select("*")
        .eq("id", app_id)
        .eq("user_id", current_user["id"])
        .execute()
    )
    if not app_result.data:
        raise HTTPException(404, "Application not found")
    application = app_result.data[0]

    # Get company
    company = db.table("companies").select("*").eq("id", application["company_id"]).execute()
    if not company.data:
        raise HTTPException(404, "Company not found")
    company = company.data[0]

    # If we have no size data at all, do a quick Apollo lookup (needed for tier-aware emails)
    apollo_revenue = None
    if company.get("employee_count") is None and not company.get("revenue"):
        search_name = _clean_company_name(company["name"])
        print(f"[Email] no size data for '{company['name']}', searching Apollo as '{search_name}'")
        org = await search_company(search_name, company.get("domain"))
        if org:
            update_data = {
                "apollo_org_id": org.get("id"),
                "industry": org.get("industry"),
                "website": org.get("website_url"),
            }
            emp_count = org.get("estimated_num_employees")
            apollo_revenue = org.get("organization_revenue")
            if emp_count:
                update_data["employee_count"] = emp_count
                company["employee_count"] = emp_count
            if apollo_revenue is not None:
                update_data["revenue"] = apollo_revenue
            print(f"[Email] Apollo: employee_count={emp_count}, revenue={apollo_revenue} for '{search_name}'")
            db.table("companies").update(update_data).eq("id", company["id"]).execute()
        else:
            print(f"[Email] Apollo returned nothing for '{search_name}'")

    # Get role template
    template = db.table("role_templates").select("*").eq("id", req.role_template_id).execute()
    if not template.data:
        raise HTTPException(404, "Template not found")
    template = template.data[0]

    # Get user profile
    profile = db.table("profiles").select("*").eq("user_id", current_user["id"]).execute()
    if not profile.data:
        raise HTTPException(404, "Profile not found")
    profile = profile.data[0]

    model = "claude-sonnet-4-6" if req.use_sonnet else "claude-haiku-4-5-20251001"

    result = await draft_email(
        user_id=current_user["id"],
        job_description=application.get("job_description"),
        company_name=company["name"],
        company_info=req.company_info,
        role_prompt_addition=template["role_prompt_addition"],
        background=profile.get("background", ""),
        projects=profile.get("projects", []),
        sign_off_block=profile["sign_off_block"],
        links_block=profile["links_block"],
        full_name=profile.get("full_name", ""),
        employee_count=company.get("employee_count"),
        revenue=apollo_revenue or company.get("revenue"),
        template_slug=template.get("slug", "swe"),
        model=model,
        previous_subject=req.previous_subject,
        previous_body=req.previous_body,
        previous_issues=req.previous_issues,
        custom_instructions=req.custom_instructions,
    )

    # Save draft + follow-up drafts to application
    db.table("applications").update({
        "email_subject": result["subject"],
        "email_body": result["body"],
        "email_status": "draft",
        "role_template_id": req.role_template_id,
        "followup_1_body": result.get("followup_1_body", ""),
        "followup_2_body": result.get("followup_2_body", ""),
        "followup_3_body": result.get("followup_3_body", ""),
    }).eq("id", app_id).execute()

    return result
