from datetime import datetime, timezone
from fastapi import APIRouter, Depends
from app.database import get_db
from app.auth.deps import get_current_user
from app.config import settings

router = APIRouter(prefix="/api", tags=["stats"])


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
