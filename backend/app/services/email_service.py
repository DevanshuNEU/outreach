import json
import re
import anthropic
from app.config import settings
from app.database import get_db


BASE_SYSTEM_PROMPT = """You write cold emails for one specific human. A builder. An engineer who thinks obsessively about how things actually work.

The goal is not to "get the job." The goal is to make one person stop, read it twice, and think: "I want to meet this person."

Most cold emails fail because they sound like everyone else. Yours won't.

━━ THE VOICE ━━
Write like you're texting a sharp friend about something you genuinely noticed, then cleaned it up into an email. Confident. Occasionally irreverent. Never desperate. Never performative.

One clever observation is worth more than five accomplishments listed.

What makes someone stop reading and start paying attention:
- A specific observation they didn't expect from a stranger
- A moment where they think "how does this person know that"
- One sentence that's just a little smarter than expected
- Confidence that implies you have options. Not that you're begging.

━━ ABSOLUTE BANS ━━
- ZERO em dashes. Zero. Use a period. Start a new sentence.
- ZERO emojis.
- ZERO: passionate, leverage, synergy, dynamic, rockstar, ninja, utilize, endeavor, spearhead, cutting-edge, game-changer, thrive, facilitate, demonstrate (say "show"), architect as a verb (say "build").
- NEVER open with "I hope this email finds you well" / "My name is" / "I am writing to express"
- NEVER say "I'd love to" (weak, needy) / "seeking opportunities" / "I believe I'd be a great fit"
- NEVER start with yourself. Start with them.

━━ WHAT TO DO INSTEAD ━━
Contractions: "I'm" not "I am". "That's" not "That is". "Don't" not "Do not".

Rhythm: Short sentence. Punchy. Then one that breathes. Then another that lands. Vary it. If a sentence has two clauses joined by "and" or "but" — make it two sentences.

Self-awareness: It's okay to briefly acknowledge this is cold outreach. "This is cold email. Here's why I sent it: [one sentence]." Then move. Don't apologize for it. Don't dwell.

Wit: Earn one clever moment per email. A frame that recontextualizes something. A contrast that reveals insight. A line that makes them smile without trying to be funny. This is NOT a joke. It's a perspective.

Humanity: One line that sounds like a specific real person wrote it. Not the kind of thing a resume generates. Something that could only come from someone who actually cares about this specific company.

━━ CARE ABOUT THEM (this is what separates great from good) ━━
Somewhere in the email, there must be a sentence that shows genuine curiosity about what THEY are building. Not "I'm excited about your mission." Something specific: a tradeoff they made, a problem they're publicly dealing with, something in their product that made you think.

The question to ask yourself: If this person reads only 2 sentences, will they know I actually looked at their work and found it interesting? If no, rewrite until yes.

Respect their time. They get 50 cold emails a week. Being brief and specific IS the respect. Padding is disrespect.

The care check: Read the email as the recipient. Is there one sentence that only someone who specifically studied THIS company could have written? If not, add it or rewrite the hook until there is.

━━ STRUCTURE (rhythm, not template) ━━
1. HOOK (1-2 sentences): About THEM. Specific enough that it could not apply to any other company. A product decision, a technical approach, something you noticed by actually looking. NOT: "I love what you're building." YES: [something only someone who used or studied their product would observe]

2. THE BRIDGE (1-2 sentences): Connect what you noticed to what you built. Not "I have experience in X." More like: "I ran into that exact problem. Here's where it led me."

3. EVIDENCE (2-3 bullets OR 1 tight paragraph): Decisions and outcomes. Not tasks. Not features. The reason you made the choice and what moved because of it.

4. THE ASK (1 sentence): Confident. Brief. Equal footing. Vary the phrasing. Options: "15 minutes?", "Worth a call this week?", "Up for a quick call?", "Want to compare notes?", "Coffee chat sometime?" Never "if you have time." Never the same CTA every email.

━━ SUBJECT LINES ━━
About THEIR product or problem. Not about you. Create a curiosity gap or make a specific claim. HARD LIMIT: 60 characters. Count every character including spaces. If it's 61, cut a word. The best subject lines make the reader think "how do they know that?" before they open.

━━ LENGTH ━━
STRICT 120 WORD MAXIMUM for the body. Count every word. If you hit 121, cut. No exceptions.

━━ IMPORTANT ━━
ONE EMAIL PER COMPANY. Same body for all contacts. Swap greeting name only.
OUTPUT: Subject: line, then body only. No greeting. No links. No sign-off. Those are added separately.
NEVER invent metrics, performance numbers, or statistics. If a number isn't explicitly in the provided background or projects, do not write it. Only use what's given."""


LINKEDIN_NOTE_PROMPT = """You write a LinkedIn connection request note. 300 character HARD LIMIT — LinkedIn will reject anything longer. Count every character including spaces.

RULES:
- This is NOT the email. It teases the email. Different angle, same person.
- Reference one specific thing about their work or company. Something that shows you looked.
- Mention you sent an email so they know to look for it.
- End with your first name only.
- No "I'd love to connect." No emojis. No em dashes. No "I'm reaching out because."
- Tone: casual, curious, human. Like a message from someone interesting, not a recruiter bot.

GOOD EXAMPLE (note: under 300 chars):
"Saw how you're handling context in [product] — had a related thought after building a RAG pipeline. Sent you an email about it. Devanshu"

BAD EXAMPLE:
"Hi! I came across your profile and I'm very passionate about your company's mission and would love to connect to discuss potential opportunities!"

Output ONLY the note text. No label. No quotes. Just the note."""


async def generate_linkedin_note(
    client: anthropic.Anthropic,
    company_name: str,
    job_title: str | None,
    email_subject: str,
    email_body: str,
    first_name: str = "Devanshu",
) -> str:
    user_msg = f"""Company: {company_name}
Role: {job_title or "Software Engineer"}
Email subject I sent them: {email_subject}
Email body I sent them: {email_body[:300]}
My first name (sign with this EXACTLY): {first_name}

Write the LinkedIn connection request note now. Under 300 characters. End with my first name exactly as written above. Output only the note."""

    response = client.messages.create(
        model="claude-haiku-4-5-20251001",
        max_tokens=120,
        system=LINKEDIN_NOTE_PROMPT,
        messages=[{"role": "user", "content": user_msg}],
    )
    note = response.content[0].text.strip().strip('"')
    # Hard truncate at 295 to be safe
    if len(note) > 295:
        note = note[:292] + "..."
    return note


JD_INSIGHT_PROMPT = """You are preparing a cold email for a software engineer. Analyze the job description and the candidate's project list.

Two tasks:
1. Extract what is SPECIFIC to this company and role (not generic industry truths)
2. Pick the 1-2 projects from the candidate's list that map MOST directly to this JD

Matching rules:
- Tokenization/encoding/BPE work in JD → pick projects with tokenization or token-level work
- Browser runtime/JavaScript/SSR/edge → pick browser or frontend-heavy projects
- DevOps/infra/Kubernetes/Terraform → pick infra projects
- Developer tooling/CLI/AI coding assistants → pick CLI or tooling projects
- RAG/retrieval/embeddings/vector search → pick retrieval projects
- General backend/distributed systems → pick backend projects
- NEVER default to the biggest or most impressive project. Pick the most RELEVANT one.

Return ONLY valid JSON:
{
  "hook": "<1 tight sentence: what this team is specifically building. Reference actual product names, tech choices, or scale challenges from the JD. Cannot apply to any other company.>",
  "challenge": "<the core engineering problem this role exists to solve, 1 sentence>",
  "lead_projects": ["<project name 1>", "<project name 2 if truly relevant>"],
  "lead_reason": "<why these projects specifically, not others, for this role — 1 sentence>"
}"""


def _extract_jd_insights(
    client: anthropic.Anthropic,
    company_name: str,
    job_description: str,
    project_names: list[str],
) -> dict:
    """Pre-step: analyze JD + pick the best-matching projects before writing the email."""
    try:
        project_list = "\n".join(f"- {n}" for n in project_names) if project_names else "No projects listed"
        msg = (
            f"Company: {company_name}\n\n"
            f"Job Description:\n{job_description[:3000]}\n\n"
            f"Candidate's projects (pick 1-2 that best match the JD):\n{project_list}"
        )
        r = client.messages.create(
            model="claude-haiku-4-5-20251001",
            max_tokens=400,
            system=JD_INSIGHT_PROMPT,
            messages=[{"role": "user", "content": msg}],
        )
        raw = r.content[0].text.strip()
        if raw.startswith("```"):
            raw = raw.split("```")[1]
            if raw.startswith("json"):
                raw = raw[4:]
        return json.loads(raw.strip())
    except Exception:
        return {}  # graceful fallback — email still drafts without it


async def draft_email(
    user_id: str,
    job_description: str | None,
    company_name: str,
    company_info: str | None,
    role_prompt_addition: str,
    background: str,
    projects: list,
    sign_off_block: str,
    links_block: str,
    full_name: str = "",
) -> dict:
    client = anthropic.Anthropic(api_key=settings.anthropic_api_key)

    # Pre-step: analyze JD + pick best-matching projects
    project_names = [p.get("name", "") for p in (projects or []) if isinstance(p, dict) and p.get("name")]
    jd_insights = {}
    if job_description:
        jd_insights = _extract_jd_insights(client, company_name, job_description, project_names)

    system = BASE_SYSTEM_PROMPT + "\n\n" + role_prompt_addition

    user_msg = f"Company: {company_name}\n"
    if company_info:
        user_msg += f"Company info: {company_info}\n"
    if job_description:
        user_msg += f"\nJob Description:\n{job_description}\n"

    # Inject JD insights — project selection is a hard instruction, rest is advisory
    if jd_insights:
        user_msg += "\n━━ RESEARCH BRIEF ━━\n"
        if jd_insights.get("hook"):
            user_msg += f"What they're specifically building: {jd_insights['hook']}\n"
        if jd_insights.get("challenge"):
            user_msg += f"Core challenge: {jd_insights['challenge']}\n"
        lead = jd_insights.get("lead_projects", [])
        if lead:
            user_msg += f"\nLEAD PROJECT INSTRUCTION (hard rule): Build the email story around: {', '.join(lead)}\n"
            if jd_insights.get("lead_reason"):
                user_msg += f"Why: {jd_insights['lead_reason']}\n"
            user_msg += "Do NOT default to a different project just because it has more metrics. Use the project that fits THIS role.\n"
        user_msg += "Hook must be specific to this company only. Rewrite until no other company could fit.\n━━━━━━━━━━━━━━━━━━━━━━━━━━\n"

    user_msg += f"\nMy Background:\n{background}\n"
    if projects:
        user_msg += "\nMy Projects:\n"
        for p in projects:
            name = p.get("name", "") if isinstance(p, dict) else ""
            desc = p.get("description", "") if isinstance(p, dict) else ""
            metrics = p.get("metrics", "") if isinstance(p, dict) else ""
            user_msg += f"- {name}: {desc}"
            if metrics:
                user_msg += f" ({metrics})"
            user_msg += "\n"
    user_msg += f"\nSender context (DO NOT include in output — frontend adds these separately):\nSign-off: {sign_off_block}\nLinks: {links_block}\n"
    user_msg += "\nDraft the cold email now. Output ONLY: Subject: line, then body. Nothing else. No greeting. No links. No sign-off. No separator lines. Subject: 60 chars MAX. Body: 120 words MAX."

    response = client.messages.create(
        model="claude-haiku-4-5-20251001",
        max_tokens=600,
        system=[{"type": "text", "text": system, "cache_control": {"type": "ephemeral"}}],
        messages=[{"role": "user", "content": user_msg}],
    )

    text = response.content[0].text.strip()

    # Parse subject and body
    subject = ""
    body = text
    if text.startswith("Subject:"):
        lines = text.split("\n", 1)
        subject = lines[0].replace("Subject:", "").strip()
        body = lines[1].strip() if len(lines) > 1 else ""

    # Strip leading separator artifacts (--- or ___) Claude sometimes adds
    body = re.sub(r'^[-_]{3,}\s*\n+', '', body).strip()

    # Extract first name from full_name for LinkedIn note sign-off
    first_name = full_name.split()[0] if full_name.strip() else "Devanshu"

    # Generate LinkedIn note using the drafted email as context
    linkedin_note = await generate_linkedin_note(
        client=client,
        company_name=company_name,
        job_title=None,
        email_subject=subject,
        email_body=body,
        first_name=first_name,
    )

    # Log usage
    db = get_db()
    input_tokens = response.usage.input_tokens
    output_tokens = response.usage.output_tokens
    # Haiku: $1/M input, $5/M output
    cost_cents = (input_tokens * 0.0001 + output_tokens * 0.0005)

    db.table("api_usage").insert({
        "user_id": user_id,
        "service": "anthropic",
        "endpoint": "email_draft",
        "tokens_in": input_tokens,
        "tokens_out": output_tokens,
        "estimated_cost_cents": round(cost_cents, 4),
    }).execute()

    return {"subject": subject, "body": body, "linkedin_note": linkedin_note}
