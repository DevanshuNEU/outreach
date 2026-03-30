"""
Deep analytics — all 10 metrics in a single endpoint.
Computes everything from existing Supabase data, no external tools.
"""

from datetime import datetime, timezone, timedelta
from collections import defaultdict
from statistics import median
from fastapi import APIRouter, Depends
from app.database import get_db
from app.auth.deps import get_current_user

router = APIRouter(prefix="/api", tags=["analytics"])

SIZE_BUCKETS = [
    (1, 50, "Startup (1-50)"),
    (51, 200, "Growth (51-200)"),
    (201, 1000, "Mid-size (201-1K)"),
    (1001, 999999, "Enterprise (1K+)"),
]


def _bucket_size(emp_count: int | None) -> str:
    if emp_count is None:
        return "Unknown"
    for lo, hi, label in SIZE_BUCKETS:
        if lo <= emp_count <= hi:
            return label
    return "Unknown"


def _parse_dt(s: str | None) -> datetime | None:
    if not s:
        return None
    try:
        return datetime.fromisoformat(s.replace("Z", "+00:00"))
    except (ValueError, TypeError):
        return None


@router.get("/analytics")
def get_analytics(current_user: dict = Depends(get_current_user)):
    db = get_db()
    uid = current_user["id"]

    # ── Fetch all data in 5 queries ──────────────────────────────────────
    outreach_res = db.table("outreach").select("*").eq("user_id", uid).execute()
    apps_res = db.table("applications").select("id, company_id, role_template_id, status, created_at").eq("user_id", uid).execute()
    contacts_res = db.table("contacts").select("id, seniority, company_id").execute()
    companies_res = db.table("companies").select("id, employee_count, name").execute()
    templates_res = db.table("role_templates").select("id, slug, title").eq("user_id", uid).execute()

    outreach = outreach_res.data or []
    apps = apps_res.data or []
    contacts = contacts_res.data or []
    companies = companies_res.data or []
    templates = templates_res.data or []

    # Build lookup maps
    app_map = {a["id"]: a for a in apps}
    contact_map = {c["id"]: c for c in contacts}
    company_map = {c["id"]: c for c in companies}
    template_map = {t["id"]: t for t in templates}

    # Only count outreach that's actually been sent
    sent_outreach = [o for o in outreach if o.get("sent_at")]
    replied_outreach = [o for o in sent_outreach if o.get("replied")]

    # ── 1. Response Rate by Company Size ─────────────────────────────────
    size_stats = defaultdict(lambda: {"sent": 0, "replied": 0})
    for o in sent_outreach:
        app = app_map.get(o.get("application_id"))
        if not app:
            continue
        company = company_map.get(app.get("company_id"))
        bucket = _bucket_size(company.get("employee_count") if company else None)
        size_stats[bucket]["sent"] += 1
        if o.get("replied"):
            size_stats[bucket]["replied"] += 1

    by_company_size = [
        {"label": k, "sent": v["sent"], "replied": v["replied"],
         "rate": round(v["replied"] / v["sent"] * 100, 1) if v["sent"] else 0}
        for k, v in sorted(size_stats.items())
    ]

    # ── 2. Response Rate by Template ─────────────────────────────────────
    tmpl_stats = defaultdict(lambda: {"sent": 0, "replied": 0, "title": ""})
    for o in sent_outreach:
        app = app_map.get(o.get("application_id"))
        if not app:
            continue
        tmpl = template_map.get(app.get("role_template_id"))
        key = tmpl["slug"] if tmpl else "none"
        tmpl_stats[key]["title"] = tmpl["title"] if tmpl else "No Template"
        tmpl_stats[key]["sent"] += 1
        if o.get("replied"):
            tmpl_stats[key]["replied"] += 1

    by_template = [
        {"slug": k, "title": v["title"], "sent": v["sent"], "replied": v["replied"],
         "rate": round(v["replied"] / v["sent"] * 100, 1) if v["sent"] else 0}
        for k, v in sorted(tmpl_stats.items(), key=lambda x: x[1]["replied"], reverse=True)
    ]

    # ── 3. Response Rate by Contact Seniority ────────────────────────────
    sen_stats = defaultdict(lambda: {"sent": 0, "replied": 0})
    for o in sent_outreach:
        contact = contact_map.get(o.get("contact_id"))
        seniority = (contact.get("seniority") or "unknown") if contact else "unknown"
        sen_stats[seniority]["sent"] += 1
        if o.get("replied"):
            sen_stats[seniority]["replied"] += 1

    by_seniority = [
        {"seniority": k, "sent": v["sent"], "replied": v["replied"],
         "rate": round(v["replied"] / v["sent"] * 100, 1) if v["sent"] else 0}
        for k, v in sorted(sen_stats.items(), key=lambda x: x[1]["replied"], reverse=True)
    ]

    # ── 4. Time to Reply ────────────────────────────────────────────────
    reply_days = []
    for o in replied_outreach:
        sent_dt = _parse_dt(o.get("sent_at"))
        reply_dt = _parse_dt(o.get("reply_date"))
        if sent_dt and reply_dt:
            diff = (reply_dt - sent_dt).total_seconds() / 86400
            if diff >= 0:
                reply_days.append(round(diff, 1))

    time_to_reply = {
        "avg": round(sum(reply_days) / len(reply_days), 1) if reply_days else None,
        "median": round(median(reply_days), 1) if reply_days else None,
        "min": min(reply_days) if reply_days else None,
        "max": max(reply_days) if reply_days else None,
        "count": len(reply_days),
    }

    # ── 5. Follow-Up Effectiveness ──────────────────────────────────────
    fu_stats = {"initial": 0, "followup_1": 0, "followup_2": 0, "followup_3": 0}
    for o in replied_outreach:
        if o.get("followup_3_sent_at"):
            fu_stats["followup_3"] += 1
        elif o.get("followup_2_sent_at"):
            fu_stats["followup_2"] += 1
        elif o.get("followup_1_sent_at"):
            fu_stats["followup_1"] += 1
        else:
            fu_stats["initial"] += 1

    total_replies = sum(fu_stats.values())
    followup_effectiveness = [
        {"stage": k.replace("_", " ").title(), "replies": v,
         "pct": round(v / total_replies * 100, 1) if total_replies else 0}
        for k, v in fu_stats.items()
    ]

    # ── 6. Optimal Contacts per Company ─────────────────────────────────
    # Group sent outreach by application, count contacts + replies
    app_contact_counts = defaultdict(lambda: {"contacts": set(), "replied": False})
    for o in sent_outreach:
        aid = o.get("application_id")
        app_contact_counts[aid]["contacts"].add(o.get("contact_id"))
        if o.get("replied"):
            app_contact_counts[aid]["replied"] = True

    contact_count_stats = defaultdict(lambda: {"apps": 0, "replied": 0})
    for data in app_contact_counts.values():
        n = len(data["contacts"])
        contact_count_stats[n]["apps"] += 1
        if data["replied"]:
            contact_count_stats[n]["replied"] += 1

    optimal_contacts = [
        {"contacts": k, "applications": v["apps"], "replied": v["replied"],
         "rate": round(v["replied"] / v["apps"] * 100, 1) if v["apps"] else 0}
        for k, v in sorted(contact_count_stats.items())
    ]

    # ── 7. Weekly Activity (last 8 weeks) ───────────────────────────────
    eight_weeks_ago = datetime.now(timezone.utc) - timedelta(weeks=8)
    weekly = defaultdict(lambda: {"sent": 0, "replied": 0})
    for o in sent_outreach:
        sent_dt = _parse_dt(o.get("sent_at"))
        if sent_dt and sent_dt >= eight_weeks_ago:
            week_key = sent_dt.strftime("%Y-W%V")
            weekly[week_key]["sent"] += 1
            if o.get("replied"):
                weekly[week_key]["replied"] += 1

    weekly_activity = [
        {"week": k, "sent": v["sent"], "replied": v["replied"]}
        for k, v in sorted(weekly.items())
    ]

    # ── 8. Best Day to Send ─────────────────────────────────────────────
    day_names = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
    day_stats = defaultdict(lambda: {"sent": 0, "replied": 0})
    for o in sent_outreach:
        sent_dt = _parse_dt(o.get("sent_at"))
        if sent_dt:
            day_stats[sent_dt.weekday()]["sent"] += 1
            if o.get("replied"):
                day_stats[sent_dt.weekday()]["replied"] += 1

    best_day = [
        {"day": day_names[k], "sent": v["sent"], "replied": v["replied"],
         "rate": round(v["replied"] / v["sent"] * 100, 1) if v["sent"] else 0}
        for k, v in sorted(day_stats.items())
    ]

    # ── 9. Pipeline Funnel ──────────────────────────────────────────────
    status_counts = defaultdict(int)
    for a in apps:
        status_counts[a.get("status", "unknown")] += 1

    funnel_order = ["drafting", "ready", "outreach_in_progress", "waiting", "replied", "closed"]
    pipeline_funnel = [
        {"stage": s.replace("_", " ").title(), "count": status_counts.get(s, 0)}
        for s in funnel_order
    ]

    # ── 10. Monthly Trends ──────────────────────────────────────────────
    monthly = defaultdict(lambda: {"applications": 0, "sent": 0, "replied": 0})
    for a in apps:
        dt = _parse_dt(a.get("created_at"))
        if dt:
            monthly[dt.strftime("%Y-%m")]["applications"] += 1

    for o in sent_outreach:
        dt = _parse_dt(o.get("sent_at"))
        if dt:
            monthly[dt.strftime("%Y-%m")]["sent"] += 1
            if o.get("replied"):
                monthly[dt.strftime("%Y-%m")]["replied"] += 1

    monthly_trends = [
        {"month": k, **v}
        for k, v in sorted(monthly.items())
    ]

    return {
        "by_company_size": by_company_size,
        "by_template": by_template,
        "by_seniority": by_seniority,
        "time_to_reply": time_to_reply,
        "followup_effectiveness": followup_effectiveness,
        "optimal_contacts": optimal_contacts,
        "weekly_activity": weekly_activity,
        "best_day": best_day,
        "pipeline_funnel": pipeline_funnel,
        "monthly_trends": monthly_trends,
        "totals": {
            "total_sent": len(sent_outreach),
            "total_replied": len(replied_outreach),
            "response_rate": round(len(replied_outreach) / len(sent_outreach) * 100, 1) if sent_outreach else 0,
        },
    }
