from datetime import datetime, timezone, timedelta
from fastapi import APIRouter, Depends
from app.database import get_db
from app.auth.deps import get_current_user
from app.config import settings

router = APIRouter(prefix="/api", tags=["stats"])

# Follow-up cadence: Day 3, Day 10, Day 17 after initial send
FOLLOWUP_CADENCE = [
    (1, 3, "followup_1_sent_at"),
    (2, 10, "followup_2_sent_at"),
    (3, 17, "followup_3_sent_at"),
]


def _get_daily_apollo_credits_used(db) -> int:
    today_start = datetime.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0).isoformat()
    result = (
        db.table("api_usage")
        .select("estimated_cost_cents")
        .eq("service", "apollo")
        .gte("created_at", today_start)
        .execute()
    )
    return sum(r.get("estimated_cost_cents", 0) or 0 for r in (result.data or []))


@router.get("/stats")
def get_stats(current_user: dict = Depends(get_current_user)):
    db = get_db()
    uid = current_user["id"]

    apps = db.table("applications").select("id", count="exact").eq("user_id", uid).execute()
    total_apps = apps.count or 0

    outreach_all = db.table("outreach").select("id, replied, sent_at", count="exact").eq("user_id", uid).execute()
    total_outreach = outreach_all.count or 0

    sent = [o for o in (outreach_all.data or []) if o.get("sent_at")]
    total_sent = len(sent)

    replied = [o for o in (outreach_all.data or []) if o.get("replied")]
    total_replied = len(replied)

    response_rate = round((total_replied / total_sent * 100), 1) if total_sent > 0 else 0

    return {
        "total_applications": total_apps,
        "total_outreach": total_outreach,
        "total_sent": total_sent,
        "total_replied": total_replied,
        "response_rate": response_rate,
    }


@router.get("/apollo/credits")
def get_apollo_credits(current_user: dict = Depends(get_current_user)):
    db = get_db()
    daily_used = _get_daily_apollo_credits_used(db)

    month_start = datetime.now(timezone.utc).replace(day=1, hour=0, minute=0, second=0, microsecond=0).isoformat()
    monthly_res = (
        db.table("api_usage")
        .select("estimated_cost_cents")
        .eq("service", "apollo")
        .gte("created_at", month_start)
        .execute()
    )
    monthly_used = sum(r.get("estimated_cost_cents", 0) or 0 for r in (monthly_res.data or []))

    return {
        "daily_used": daily_used,
        "daily_limit": settings.apollo_daily_credit_limit,
        "daily_remaining": max(0, settings.apollo_daily_credit_limit - daily_used),
        "monthly_used": monthly_used,
        "monthly_total": 2515,
        "monthly_remaining": max(0, 2515 - monthly_used),
        "max_per_search": settings.apollo_max_contacts_per_search,
    }


@router.get("/usage")
def get_usage(current_user: dict = Depends(get_current_user)):
    db = get_db()
    uid = current_user["id"]

    # User's usage
    user_usage = (
        db.table("api_usage")
        .select("service, endpoint, tokens_in, tokens_out, estimated_cost_cents, created_at")
        .eq("user_id", uid)
        .order("created_at", desc=True)
        .limit(100)
        .execute()
    )

    # Aggregate by service
    anthropic_cost = sum(
        r.get("estimated_cost_cents", 0) or 0
        for r in (user_usage.data or [])
        if r["service"] == "anthropic"
    )
    anthropic_calls = sum(
        1 for r in (user_usage.data or []) if r["service"] == "anthropic"
    )
    apollo_calls = sum(
        1 for r in (user_usage.data or []) if r["service"] == "apollo"
    )

    # Global Apollo usage (shared across all users) - daily
    all_apollo = (
        db.table("api_usage")
        .select("id", count="exact")
        .eq("service", "apollo")
        .execute()
    )

    return {
        "user": {
            "anthropic_cost_cents": round(anthropic_cost, 2),
            "anthropic_calls": anthropic_calls,
            "apollo_calls": apollo_calls,
        },
        "global": {
            "apollo_total_calls": all_apollo.count or 0,
            "apollo_daily_limit": 2000,
            "apollo_rate_limit_per_min": 200,
        },
        "recent": user_usage.data[:20] if user_usage.data else [],
    }


def _compute_next_followup(outreach_row: dict, now: datetime) -> dict | None:
    """For a single outreach row, return the next follow-up due (or None if all done/replied)."""
    if outreach_row.get("replied"):
        return None
    sent_at_str = outreach_row.get("sent_at")
    if not sent_at_str:
        return None

    sent_at = datetime.fromisoformat(sent_at_str.replace("Z", "+00:00"))
    for fu_num, days_after, field in FOLLOWUP_CADENCE:
        if outreach_row.get(field):
            continue  # already sent this follow-up
        due_date = sent_at + timedelta(days=days_after)
        is_overdue = now >= due_date
        days_until = (due_date - now).days
        return {
            "followup_number": fu_num,
            "due_date": due_date.isoformat(),
            "is_overdue": is_overdue,
            "days_until": days_until,  # negative = overdue by N days
        }
    return None  # all 3 follow-ups already sent


@router.get("/followup-queue")
def get_followup_queue(current_user: dict = Depends(get_current_user)):
    db = get_db()
    uid = current_user["id"]
    now = datetime.now(timezone.utc)

    # Get all outreach that's been sent but not replied to
    outreach_res = (
        db.table("outreach")
        .select("*, contacts(*)")
        .eq("user_id", uid)
        .eq("replied", False)
        .execute()
    )
    rows = outreach_res.data or []

    # Filter to only rows with actual sent_at value
    rows = [r for r in rows if r.get("sent_at")]

    if not rows:
        return {"overdue": [], "due_today": [], "upcoming": [], "total_due": 0}

    # Batch-fetch applications + companies
    app_ids = list({r["application_id"] for r in rows})
    apps_res = (
        db.table("applications")
        .select("id, job_title, company_id, companies(name, location)")
        .in_("id", app_ids)
        .execute()
    )
    app_map = {a["id"]: a for a in (apps_res.data or [])}

    overdue = []
    due_today = []
    upcoming = []

    for row in rows:
        fu = _compute_next_followup(row, now)
        if not fu:
            continue

        app = app_map.get(row["application_id"], {})
        company = app.get("companies") or {}
        contact = row.get("contacts") or {}

        item = {
            "outreach_id": row["id"],
            "application_id": row["application_id"],
            "followup_number": fu["followup_number"],
            "followup_field": FOLLOWUP_CADENCE[fu["followup_number"] - 1][2],
            "due_date": fu["due_date"],
            "days_until": fu["days_until"],
            "is_overdue": fu["is_overdue"],
            "contact_name": f"{contact.get('first_name', '')} {contact.get('last_name', '')}".strip(),
            "contact_email": contact.get("email", ""),
            "company_name": company.get("name", "Unknown"),
            "job_title": app.get("job_title", ""),
        }

        if fu["is_overdue"] and fu["days_until"] < 0:
            overdue.append(item)
        elif fu["days_until"] == 0:
            due_today.append(item)
        elif fu["days_until"] <= 3:
            upcoming.append(item)

    # Sort: most overdue first, then by due date
    overdue.sort(key=lambda x: x["days_until"])
    upcoming.sort(key=lambda x: x["days_until"])

    return {
        "overdue": overdue,
        "due_today": due_today,
        "upcoming": upcoming,
        "total_due": len(overdue) + len(due_today),
    }
