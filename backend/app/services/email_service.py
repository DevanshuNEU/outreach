import json
import re
import anthropic
from app.config import settings
from app.database import get_db


BASE_SYSTEM_PROMPT = """You write cold emails for a real human. Not an applicant. A builder who has shipped real things and genuinely cares about the craft.

━━ THE PSYCHOLOGY (internalize this before writing a single word) ━━

The goal is NOT to impress. The goal is to make one person feel SEEN.

When someone reads your email and thinks "how does this person know that about us?" they reply. Not because of metrics. Not because of a resume. Because you showed genuine understanding of THEIR world.

Here is how humans actually decide to reply to cold emails:

1. RECIPROCITY: Give before you ask. A genuine, specific observation about their work is a gift. It proves effort. When someone gives you something thoughtful, you feel compelled to respond.

2. IDENTITY VALIDATION: Don't flatter. Understand. "I admire your company" is flattery (delete). "Your move to [specific thing] makes sense because [specific reason]" is understanding (reply).

3. CURIOSITY GAP: The subject line opens a loop. The body closes it. The reader should feel a pull to open the email because there's something they need to resolve.

4. SPECIFICITY IS UNFAKEABLE AT SCALE: One specific detail about their company proves this isn't a mass blast. It's the single strongest signal of genuine interest. A sentence that could only apply to THIS company is worth more than any metric.

5. PATTERN INTERRUPT: Most cold emails look identical. One unexpected moment of honesty, one unusually specific observation, one structural surprise, makes the brain switch from "scanning" to "reading."

━━ THE VOICE ━━
Write like a sharp builder talking to another builder. Confident but not cocky. Direct but not cold. One moment of genuine warmth or curiosity per email. Not performative enthusiasm. Real interest.

The vulnerability-confidence ratio: 80% confident, 20% human. The humanity makes the confidence believable. One moment of "here's what I actually think" or "I've been chewing on this problem too" is more powerful than five achievement bullets.

Short sentences. Varied rhythm. A one-line paragraph after two longer ones. Periods over question marks. Statements over hedges.

━━ ABSOLUTE BANS ━━
- ZERO em dashes (use a period, start a new sentence)
- ZERO emojis
- ZERO: passionate, leverage, synergy, dynamic, rockstar, ninja, utilize, endeavor, spearhead, cutting-edge, game-changer, thrive, facilitate, demonstrate (say "show"), architect as a verb
- NEVER open with "I hope this email finds you well" / "My name is" / "I am writing to"
- NEVER: "I'd love to" / "seeking opportunities" / "I believe I'd be a great fit"
- NEVER start the email with "I". First word must be about them or their company.
- Contractions always: "I'm" not "I am", "don't" not "do not", "that's" not "that is"

━━ THE I/YOU RATIO ━━
Count references to "I/my/me" vs "you/your/[company name]". The email MUST have at least as many you/company references as I/my references. If the email is all "I built, I did, I shipped" it reads as a monologue, not a conversation. Rewrite until balanced.

━━ THE "SO WHAT?" TEST ━━
Every single sentence must survive this test: if the reader thinks "so what?" after reading it, cut it or rewrite it. "I'm a software engineer" fails. "I brought p95 from 800ms to 280ms before anyone suggested adding servers" passes.

━━ STRUCTURE ━━

1. HOOK (1-2 sentences): About THEM. Something specific you noticed about their product, technical approach, a recent decision, or a problem they're publicly tackling. This must be a genuine observation, not a compliment. It should make them think "this person actually looked at what we do." It CANNOT apply to any other company. If it could, rewrite.

2. BRIDGE (1-2 sentences): Connect what you noticed to what you've built. Not "I have experience in X." More like: "I hit that exact wall" or "That's the constraint I ended up building around." This should feel like a natural conversation, not a pivot to your resume.

3. PROOF (2-3 compact sentences): ONE project. The single most relevant one. Go deep on the decision and outcome. Do NOT mention a second project unless it is genuinely, directly relevant to their specific challenge. If in doubt, leave it out. One deep story beats two shallow mentions every time.

4. THE CLOSE (1-2 sentences): This is the most important part. Two things must happen:
   a) A brief "why me" punch: one sentence that makes them think "this person ships real things." Not a brag. A fact. Something like "Three tools live in production right now, each solving a different hard problem." Or: "I ship complete systems solo, fast, and they stay up."
   b) A CLEAR ask for a call. Not a question about their work. Not a vague "let me know." A direct ask for time:
   - "Would love a quick call to dig into this. Open this week?"
   - "Worth 15 minutes? Happy to walk through any of this live."
   - "I'd welcome a call to talk about how I can help here."
   NEVER end with just a technical question. NEVER end without asking for time. The reader must finish the email knowing exactly what you want: a call.

━━ SUBJECT LINES ━━
About THEIR product or problem. Not about you. Not about what you built.
Create a curiosity gap: the reader should think "what does this person know?" before opening.
3-7 words. Lowercase is fine. Specific beats clever.
HARD LIMIT: 60 characters including spaces.

BAD: "Full-stack engineer interested in your team" (about you, generic)
BAD: "Real-time token counting in Claude's API" (about your project)
GOOD: "your kafka migration and context windows" (specific to them, curiosity gap)
GOOD: "the tradeoff in your local-first sync" (shows you studied their work)

━━ LENGTH ━━
HARD MAXIMUM: 110 WORDS for the body. Not 111. Not 115. Not 120. ONE HUNDRED AND TEN.
Count every word before outputting. If you're over, cut the weakest sentence. The weakest sentence is usually in the PROOF section — cut the project mention that's least relevant.
DO NOT add a second project just to fill space. ONE relevant project with ONE sharp result is always better than two projects where one is shoehorned in.

━━ ANTI-FILLER RULE ━━
If you mention more than ONE project in the PROOF section, check: does the second project DIRECTLY connect to THIS company's specific challenge? If the connection requires more than one logical leap, CUT IT. One focused story beats two diluted ones.

━━ OUTPUT FORMAT ━━
ONE EMAIL PER COMPANY. Same body for all contacts. Only the greeting name changes.
Output ONLY: Subject: line, then body. No greeting. No links. No sign-off. Those are added separately by the frontend.

CRITICAL — NEVER INVENT:
- NEVER invent metrics, performance numbers, percentages, or statistics
- NEVER write a number that is not EXPLICITLY provided in the background or projects section below
- If a project description says "87.5% Hit@1" you can use that number. If it doesn't mention a specific number, DO NOT make one up.
- Violating this rule destroys credibility. One fake number invalidates the entire email.

No em dashes anywhere. No separator lines (--- or ___) before or after the body."""


LINKEDIN_NOTE_PROMPT = """You write a LinkedIn connection request note. 300 character HARD LIMIT. Count every character including spaces.

RULES:
- This is NOT the email repeated. It's a separate touch that makes them curious.
- Reference one specific thing about their work or company. Something that shows you looked.
- Mention you sent an email so they check their inbox.
- End with your first name only.
- No "I'd love to connect." No emojis. No em dashes. No "I'm reaching out because."
- Tone: casual, specific, human. Like a note from someone who actually looked at their work.
- NEVER invent a person's name. Only use names explicitly provided.

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


JD_INSIGHT_PROMPT = """You are preparing a cold email for a software engineer targeting a specific company. Your job is to deeply understand the COMPANY and what would make someone there feel SEEN.

TASK 1 — UNDERSTAND THEIR WORLD:
Read the job description carefully. Extract what is SPECIFIC to this company. Not generic industry truths. What are they actually building? What technical decisions have they made? What's hard about their problem?

TASK 2 — FIND THE "SEEN" MOMENT:
What specific observation about this company's approach, product, or technical challenge would make a reader think "this person actually studied what we do"? This is the most important output. It must be something that could NOT apply to any other company.

TASK 3 — MATCH PROJECTS (HONESTY IS CRITICAL):
Pick 1-2 projects from the candidate's list that map MOST directly to this JD's specific challenges.

Matching rules:
- Match by the PROBLEM being solved, not by surface-level technology overlap
- If the JD is about agentic AI systems, pick projects that show autonomous system design
- If the JD is about small team / ownership, emphasize solo-shipped production tools
- If the JD is about performance at scale, pick production optimization work
- NEVER default to the biggest or most impressive project. Pick the most RELEVANT one.

HONESTY CHECK — this is the most important rule:
- If NO project is a genuine, direct match for this company's domain, set "match_quality" to "weak"
- A Chrome extension is NOT a "data pipeline validation system"
- A Terraform provisioning tool is NOT a "sandboxing system"
- Do NOT reframe a project as something it's not just to force a connection
- When match_quality is "weak", the email should lead with the BUILDER STORY (solo-shipped multiple production tools, ownership mentality, production performance experience) rather than forcing a single project to carry the email

TASK 4 — CRAFT A HUMAN CTA:
Based on the company's specific challenge, suggest a CTA that offers value or sparks curiosity. Not "15 minutes?" but something tied to their problem.

Return ONLY valid JSON:
{
  "their_world": "<1-2 sentences: what this company is specifically building and why it's technically hard>",
  "seen_moment": "<1 sentence: a specific observation about their approach/product/tech that would make them feel understood. Must be unfakeable — something only someone who actually studied this company would say>",
  "their_hard_problem": "<1 sentence: the core constraint or challenge this role exists to solve>",
  "match_quality": "<'strong' if a project directly solves a similar problem, 'weak' if the connection requires reframing the project as something it's not>",
  "lead_projects": ["<project name 1>", "<optional project name 2>"],
  "lead_reason": "<1 sentence: why these projects map to this challenge. If weak match, say so honestly>",
  "builder_angle": "<if match_quality is weak: 1 sentence about the builder story to lead with instead. e.g. 'Solo-shipped 3 production tools, each solving a different hard problem. Ownership mentality.'>",
  "human_cta": "<1-2 sentences: First a quick 'why me' punch (e.g. 'Three tools live in production right now'). Then ask for a call tied to their challenge. MUST ask for time. e.g. 'Worth a quick call this week?' Keep it confident and direct. The reader must finish knowing you want a call.>"
}"""


def _extract_jd_insights(
    client: anthropic.Anthropic,
    company_name: str,
    job_description: str,
    project_names: list[str],
) -> dict:
    """Pre-step: analyze JD + company deeply, pick best-matching projects, craft human CTA."""
    try:
        project_list = "\n".join(f"- {n}" for n in project_names) if project_names else "No projects listed"
        msg = (
            f"Company: {company_name}\n\n"
            f"Job Description:\n{job_description[:3000]}\n\n"
            f"Candidate's projects (pick 1-2 that best match the JD):\n{project_list}"
        )
        r = client.messages.create(
            model="claude-haiku-4-5-20251001",
            max_tokens=500,
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


def _get_email_tier(employee_count: int | None = None, revenue: float | None = None) -> str:
    """Determine email strategy tier based on company size or revenue.

    Apollo Basic plan often returns employee_count=None, so we fall back to revenue:
    - <$5M revenue → startup
    - $5M-$100M → growth
    - $100M-$1B → midsize
    - >$1B → enterprise
    """
    if employee_count is not None:
        if employee_count <= 50:
            return "startup"
        elif employee_count <= 500:
            return "growth"
        elif employee_count <= 5000:
            return "midsize"
        return "enterprise"

    if revenue is not None and revenue > 0:
        if revenue < 5_000_000:
            return "startup"
        elif revenue < 100_000_000:
            return "growth"
        elif revenue < 1_000_000_000:
            return "midsize"
        return "enterprise"

    return "growth"  # safe default when we have no data


ENTERPRISE_SYSTEM_PROMPT = """You write concise, professional emails from a new grad to a recruiter at a large company.

This is NOT a cold outreach to a startup founder. This is a formal application email to a university/technical recruiter at a large enterprise. The reader processes hundreds of candidates. They need clarity, not cleverness.

━━ WHAT RECRUITERS CARE ABOUT (in order) ━━
1. Graduation date and degree
2. Work authorization status (OPT/STEM OPT = no sponsorship needed = HUGE plus)
3. Relevant technical skills matching the JD
4. 1-2 concrete project highlights with metrics
5. Availability

━━ STRUCTURE ━━
1. OPENER (1 sentence): State the role you're targeting and one line showing you know the company.
2. QUALIFICATIONS (2-3 sentences): Degree, grad date, key skills matching the JD. Mention OPT/STEM OPT explicitly.
3. PROOF (2-3 sentences): 1-2 most relevant projects with real metrics. Keep it tight.
4. CLOSE (1-2 sentences): Ask directly for an interview. Be clear and confident. Examples:
   - "I'd love the opportunity to interview for this role. Resume is attached."
   - "Would welcome the chance to interview. Resume attached for your review."
   - "I'd appreciate the opportunity to discuss this role in an interview. Resume is attached."
   ALWAYS ask for the interview explicitly. ALWAYS mention resume is attached.

━━ RULES ━━
- ZERO em dashes. Use periods.
- Contractions are fine: "I'm" not "I am"
- Professional but not stiff. Confident but not cocky.
- Do NOT try to be clever or create curiosity gaps. Be clear and direct.
- NEVER invent metrics or numbers not in the provided background/projects.
- First word should be about the company or role, not "I".
- HARD MAX: 100 words for body.

━━ SUBJECT LINE ━━
Format: "[Degree] [Grad Date] — [Role] — STEM OPT, No Sponsorship"
Example: "MS SWE May 2026 — Software Engineer — STEM OPT, no sponsorship needed"
Keep under 70 chars.

━━ OUTPUT FORMAT ━━
Subject: line, then body. No greeting. No links. No sign-off. Those are added separately."""


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
    employee_count: int | None = None,
    revenue: float | None = None,
) -> dict:
    client = anthropic.Anthropic(api_key=settings.anthropic_api_key)

    tier = _get_email_tier(employee_count=employee_count, revenue=revenue)
    is_enterprise = tier == "enterprise"
    print(f"[Email] company={company_name}, employee_count={employee_count}, revenue={revenue}, tier={tier}, enterprise={is_enterprise}")

    # Pre-step: deeply analyze JD + pick best-matching projects (skip for enterprise — recruiters don't care about curiosity gaps)
    project_names = [p.get("name", "") for p in (projects or []) if isinstance(p, dict) and p.get("name")]
    jd_insights = {}
    if job_description and not is_enterprise:
        jd_insights = _extract_jd_insights(client, company_name, job_description, project_names)

    if is_enterprise:
        system = ENTERPRISE_SYSTEM_PROMPT + "\n\n" + role_prompt_addition
    else:
        system = BASE_SYSTEM_PROMPT + "\n\n" + role_prompt_addition

    user_msg = f"Company: {company_name}\n"
    if company_info:
        user_msg += f"Company info: {company_info}\n"
    if job_description:
        user_msg += f"\nJob Description:\n{job_description}\n"

    # For non-enterprise: inject deep company intelligence
    if jd_insights and not is_enterprise:
        user_msg += "\n━━ COMPANY INTELLIGENCE (use this to make them feel SEEN) ━━\n"
        if jd_insights.get("their_world"):
            user_msg += f"What they're building and why it's hard: {jd_insights['their_world']}\n"
        if jd_insights.get("seen_moment"):
            user_msg += f"THE KEY OBSERVATION (weave this into the hook — this is what makes them think 'this person gets us'): {jd_insights['seen_moment']}\n"
        if jd_insights.get("their_hard_problem"):
            user_msg += f"The core challenge this role solves: {jd_insights['their_hard_problem']}\n"
        match_quality = jd_insights.get("match_quality", "strong")
        lead = jd_insights.get("lead_projects", [])
        if match_quality == "weak":
            builder_angle = jd_insights.get("builder_angle", "Solo-shipped multiple production tools with full ownership.")
            user_msg += f"\nMATCH QUALITY: WEAK. Do NOT force a project to fit. Instead:\n"
            user_msg += f"BUILDER STORY INSTRUCTION: Lead the proof section with this angle: {builder_angle}\n"
            user_msg += "Mention projects briefly as EVIDENCE of range and shipping ability, NOT as direct parallels to their problem.\n"
            user_msg += "Do NOT reframe a project as something it's not. A Chrome extension is NOT a data pipeline. A Terraform tool is NOT a sandbox.\n"
            if lead:
                user_msg += f"Reference projects: {', '.join(lead)} (but describe them honestly, as what they actually are)\n"
        elif lead:
            user_msg += f"\nPROJECT INSTRUCTION (hard rule): Build the email around: {', '.join(lead)}\n"
            if jd_insights.get("lead_reason"):
                user_msg += f"Why: {jd_insights['lead_reason']}\n"
            user_msg += "Do NOT default to a different project just because it has more metrics. Use what fits THIS role.\n"
        if jd_insights.get("human_cta"):
            user_msg += f"\nCTA INSTRUCTION: Use this as the ask (adapt the wording naturally): {jd_insights['human_cta']}\n"
        user_msg += "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"

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

    if is_enterprise:
        word_limit = 100
        user_msg += f"\nDraft the email now. Output ONLY: Subject: line, then body. Nothing else. No greeting. No links. No sign-off. No separator lines. No em dashes. Subject format: 'MS SWE May 2026 . [Role] . STEM OPT, no sponsorship needed' (under 70 chars). Body: {word_limit} words HARD MAX. First word MUST be about the company or role, not 'I'."
        user_msg += "\n\nCRITICAL — THE LAST SENTENCE OF THE BODY MUST ask for an interview. Examples: 'I'd love the opportunity to interview for this role. Resume is attached.' or 'Would welcome the chance to interview. Resume attached.' DO NOT end the email without explicitly asking for an interview and mentioning resume attached."
    else:
        word_limit = 110
        user_msg += f"\nDraft the cold email now. Output ONLY: Subject: line, then body. Nothing else. No greeting. No links. No sign-off. No separator lines. No em dashes. Subject: 60 chars MAX. Body: {word_limit} words HARD MAX (count before output — if over {word_limit}, delete the weakest sentence). First word of the email MUST be about them, not 'I'. Do NOT mention more than one project unless both are directly relevant."
        user_msg += "\n\nCRITICAL — THE LAST SENTENCE OF THE BODY MUST ask for a call or conversation. Examples: 'Worth a quick call this week?' or 'Would love 15 minutes to dig into this.' or 'Open to a quick call?' DO NOT end with just a technical question. DO NOT end without asking for time. The reader must finish the email knowing you want a call."

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

    # Kill em dashes
    body = body.replace('—', '. ').replace('–', '. ')
    body = re.sub(r'\.\s+\.', '.', body)
    subject = subject.replace('—', ': ').replace('–', ': ')

    # Hard-enforce word limit by trimming at sentence boundary
    max_words = 100 if is_enterprise else 120
    words = body.split()
    if len(words) > max_words:
        truncated = ' '.join(words[:max_words])
        last_period = truncated.rfind('.')
        last_question = truncated.rfind('?')
        cut_point = max(last_period, last_question)
        if cut_point > len(truncated) // 2:
            body = truncated[:cut_point + 1].strip()
        else:
            body = truncated.strip()

    # Hard-enforce subject char limit (70 for enterprise, 60 for others)
    max_subject = 70 if is_enterprise else 60
    if len(subject) > max_subject:
        cut = subject[:max_subject].rfind(" ")
        subject = subject[:cut] if cut > max_subject // 2 else subject[:max_subject]

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
