from pydantic import BaseModel
from datetime import datetime


# ── Auth ──
class RegisterRequest(BaseModel):
    username: str
    password: str


class LoginRequest(BaseModel):
    username: str
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


class UserOut(BaseModel):
    id: str
    username: str
    created_at: str | None = None


# ── Profile ──
class ProjectItem(BaseModel):
    name: str
    description: str
    metrics: str | None = None
    url: str | None = None


class ProfileUpdate(BaseModel):
    full_name: str | None = None
    background: str | None = None
    sign_off_block: str | None = None
    links_block: str | None = None
    projects: list[ProjectItem] | None = None


class ProfileOut(BaseModel):
    id: str
    user_id: str
    full_name: str
    background: str | None = None
    sign_off_block: str
    links_block: str
    projects: list | None = None


# ── Templates ──
class TemplateCreate(BaseModel):
    slug: str
    title: str
    color: str = "#3b82f6"
    tagline: str | None = None
    system_prompt: str
    role_prompt_addition: str
    example_email: str | None = None
    sort_order: int = 0


class TemplateUpdate(BaseModel):
    title: str | None = None
    color: str | None = None
    tagline: str | None = None
    system_prompt: str | None = None
    role_prompt_addition: str | None = None
    example_email: str | None = None
    sort_order: int | None = None


class TemplateOut(BaseModel):
    id: str
    user_id: str
    slug: str
    title: str
    color: str
    tagline: str | None = None
    system_prompt: str
    role_prompt_addition: str
    example_email: str | None = None
    sort_order: int


# ── Companies ──
class CompanyCreate(BaseModel):
    name: str
    domain: str | None = None
    location: str | None = None


class CompanyOut(BaseModel):
    id: str
    name: str
    domain: str | None = None
    location: str | None = None
    apollo_org_id: str | None = None
    employee_count: int | None = None
    industry: str | None = None
    website: str | None = None


# ── Applications ──
class ApplicationCreate(BaseModel):
    company_id: str
    role_template_id: str | None = None
    job_title: str | None = None
    job_url: str | None = None
    job_description: str | None = None


class ApplicationUpdate(BaseModel):
    role_template_id: str | None = None
    job_title: str | None = None
    job_url: str | None = None
    job_description: str | None = None
    email_subject: str | None = None
    email_body: str | None = None
    email_status: str | None = None
    status: str | None = None
    notes: str | None = None
    linkedin_note: str | None = None


class NextFollowUp(BaseModel):
    followup_number: int
    due_date: str
    is_overdue: bool


class ApplicationOut(BaseModel):
    id: str
    user_id: str
    company_id: str
    role_template_id: str | None = None
    job_title: str | None = None
    job_url: str | None = None
    job_description: str | None = None
    email_subject: str | None = None
    email_body: str | None = None
    email_status: str
    status: str
    notes: str | None = None
    linkedin_note: str | None = None
    contact_count: int = 0
    next_followup: NextFollowUp | None = None
    has_reply: bool = False
    created_at: str | None = None
    updated_at: str | None = None


# ── Email Drafting ──
class DraftEmailRequest(BaseModel):
    role_template_id: str
    company_info: str | None = None
    use_sonnet: bool = False


# ── Contacts ──
class ContactOut(BaseModel):
    id: str
    company_id: str
    apollo_person_id: str | None = None
    first_name: str
    last_name: str
    title: str | None = None
    seniority: str | None = None
    email: str | None = None
    email_status: str | None = None
    linkedin_url: str | None = None


# ── Outreach ──
class OutreachCreate(BaseModel):
    application_id: str
    contact_id: str


class OutreachUpdate(BaseModel):
    sent_at: str | None = None
    replied: bool | None = None
    reply_date: str | None = None
    followup_1_sent_at: str | None = None
    followup_2_sent_at: str | None = None
    followup_3_sent_at: str | None = None
    notes: str | None = None


class OutreachOut(BaseModel):
    id: str
    application_id: str
    contact_id: str
    user_id: str
    personalized_greeting: str | None = None
    sent_at: str | None = None
    followup_1_sent_at: str | None = None
    followup_2_sent_at: str | None = None
    followup_3_sent_at: str | None = None
    replied: bool
    reply_date: str | None = None
    notes: str | None = None
    created_at: str | None = None
    contact: ContactOut | None = None
