from fastapi import APIRouter, Depends, HTTPException
from app.database import get_db
from app.auth.deps import get_current_user
from app.models.schemas import DraftEmailRequest
from app.services.email_service import draft_email

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
    )

    # Save draft to application
    db.table("applications").update({
        "email_subject": result["subject"],
        "email_body": result["body"],
        "email_status": "draft",
        "role_template_id": req.role_template_id,
    }).eq("id", app_id).execute()

    return result
