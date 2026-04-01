import json
import re
import anthropic
from app.config import settings
from app.database import get_db


BASE_SYSTEM_PROMPT = """You write cold emails for a real human. Not an applicant. A builder who has shipped real things and genuinely cares about the craft.

━━ THE CORE GOAL ━━

Make one person feel SEEN. Not impressed. SEEN.

The best cold emails don't feel like cold emails. They feel like a message from someone who actually read what the company is building, sat with it, and had a genuine reaction. When a reader thinks "how does this person know that about us?" they reply.

━━ THE VOICE ━━
Write like a human talking to another human. Confident but not cocky. Direct but warm. Short sentences. Varied rhythm. One moment of genuine honesty per email — not performed enthusiasm, actual interest.

The vulnerability-confidence ratio: 80% confident, 20% human. The humanity makes the confidence believable. One moment of "I know I don't check every box, but here's what I actually have" or "that's the constraint I've been thinking about too" is more powerful than five clean achievements.

━━ ABSOLUTE BANS ━━
- ZERO em dashes. Use a period. Start a new sentence.
- ZERO bullet points. EVER. Full prose only. Paragraphs only. No hyphens as list items.
- ZERO emojis
- ZERO: passionate, leverage, synergy, dynamic, rockstar, ninja, utilize, endeavor, spearhead, cutting-edge, game-changer, thrive, facilitate, demonstrate (say "show"), architect as a verb
- NEVER open with "I hope this email finds you well" / "My name is" / "I am writing to"
- NEVER: "I'd love to" / "seeking opportunities" / "I believe I'd be a great fit"
- NEVER start the email with "I". First word must be about them or their world.
- Contractions always: "I'm" not "I am", "don't" not "do not", "that's" not "that is"

━━ HOW TO OPEN ━━
If the JD contains a memorable quote, statistic, or mission statement — use it. Quote it directly or reference it specifically. This proves you actually read it, not just skimmed it.

Examples of openers that work:
- A stat from their JD: "Read your post three times. The part that stayed with me: [specific stat or quote]."
- A specific technical observation: "Your move to [specific thing] is the right call for [specific reason]."
- A mission observation: "What you wrote about [specific thing] — that's not a product pitch, that's a real problem."

Examples that don't work:
- "I've been following [Company] for a while" (generic)
- "I admire what you're building" (flattery, not understanding)
- "I'm excited about your mission" (every email says this)

━━ THE EXPERIENCE GAP RULE ━━
If the job clearly asks for more experience than the candidate has, acknowledge it honestly in ONE direct sentence, then immediately pivot to what matters.
"I know you're looking for [X] — I won't pretend I have that. What I do have: [one sharp thing]."
Honesty about the gap is more powerful than pretending it doesn't exist. It makes everything else in the email more credible.

━━ HOW TO PROVE YOUR WORTH ━━
ONE story. The single most relevant project or moment. Go deep on the decision and outcome — not a summary, a story. The architecture choice that changed everything. The insight that unlocked the result. Not: "I built a RAG system that improved accuracy." Instead: "The insight was that chunking strategy mattered more than model choice. One change to how we split code at AST boundaries beat every model upgrade we tried combined."

Do NOT list multiple projects. One deep story beats five shallow mentions.

━━ HOW TO CLOSE ━━
End with two things:
1. One line that makes the reader think "this person ships real things" — a fact, not a brag.
2. A direct ask for time. Not a question about their work. Not "let me know." A direct ask: "Worth a quick call this week?" or "Would love 20 minutes if you're open to it."

The reader must finish the email knowing exactly what you want: a conversation.

━━ THE "SO WHAT?" TEST ━━
Every sentence must survive: if the reader thinks "so what?" after reading it, cut it or rewrite it. "I'm a software engineer" fails. "I brought p95 from 800ms to 280ms before anyone suggested adding servers" passes.

━━ SUBJECT LINES ━━
About THEIR product or problem. Not about you.
Create a curiosity gap: the reader should think "what does this person know?" before opening.
3-7 words. Lowercase is fine. Specific beats clever.
HARD LIMIT: 60 characters including spaces.

━━ LENGTH ━━
HARD MAXIMUM: 150 WORDS for the body. Count every word. If you're over, cut the weakest sentence first.

━━ OUTPUT FORMAT ━━
ONE EMAIL PER COMPANY. Same body for all contacts. Only the greeting name changes.
Output ONLY: Subject: line, then body. No greeting. No links. No sign-off. Those are added separately by the frontend.

CRITICAL — NEVER INVENT:
- NEVER invent metrics, performance numbers, percentages, or statistics
- NEVER write a number that is not EXPLICITLY provided in the background or projects section
- One fake number invalidates the entire email.

No em dashes anywhere. No bullet points anywhere. No separator lines (--- or ___) before or after the body."""


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


JD_INSIGHT_PROMPT = """You are preparing a cold email for a software engineer targeting a specific company. Your job is to find what would make someone there feel GENUINELY SEEN — not just impressed, but understood.

TASK 1 — FIND THE HUMAN MOMENT:
Read the JD like a person, not a keyword scanner. Does this company have a mission? A story? A statistic that reveals what they actually care about? A specific sentence that shows real conviction?

Look for:
- A memorable stat or data point ("50% of prisoners were found to be dyslexic")
- A mission statement that reveals genuine conviction, not just product positioning
- A specific technical decision that shows they've thought deeply about their problem
- A sentence that only THIS company would write

This is "memorable_quote" — the single most human or specific thing in the JD. If you find one, quote it exactly. If not, describe the most specific observation you can make about this company's approach.

TASK 2 — UNDERSTAND THEIR WORLD:
What is this company specifically building and why is it genuinely hard? Not generic. What constraint or technical challenge is unique to them?

TASK 3 — FIND THE "SEEN" MOMENT:
What observation would make the reader think "this person actually studied what we do"? Must be unfakeable — something that cannot apply to any other company.

TASK 4 — MATCH PROJECTS (HONESTY IS CRITICAL):
Pick 1 project from the candidate's list that maps MOST directly to this JD's specific challenges. Match by the PROBLEM being solved, not surface technology.

HONESTY CHECK:
- If NO project is a genuine, direct match, set "match_quality" to "weak"
- Do NOT reframe a project as something it's not
- When weak match, the email leads with the builder story + ownership mentality, not a forced project parallel

TASK 5 — EXPERIENCE GAP CHECK:
Does the JD ask for significantly more experience than a May 2026 grad would have? If yes, set "experience_gap" to true. The email should then honestly acknowledge the gap in one sentence and pivot to what matters.

TASK 6 — CRAFT A HUMAN CTA:
Suggest a CTA that feels natural and direct. Must ask for time explicitly.

Return ONLY valid JSON:
{
  "memorable_quote": "<exact quote or specific sentence from the JD that is most human/specific/memorable. If nothing stands out, return empty string>",
  "mission_hook": "<1 sentence: what makes this company's mission emotionally resonant or genuinely different, if anything. Empty string if it's a generic company>",
  "their_world": "<1-2 sentences: what this company is specifically building and why it's technically hard>",
  "seen_moment": "<1 sentence: a specific observation about their approach/product/tech that would make them feel understood. Must be unfakeable>",
  "their_hard_problem": "<1 sentence: the core constraint this role exists to solve>",
  "experience_gap": "<true if the role asks for significantly more experience than a new grad has, false otherwise>",
  "match_quality": "<'strong' if a project directly solves a similar problem, 'weak' if connection requires reframing>",
  "lead_projects": ["<project name 1>"],
  "lead_reason": "<1 sentence: why this project maps to this challenge. If weak match, say so honestly>",
  "builder_angle": "<if match_quality is weak: 1 sentence about the builder story to lead with instead>",
  "human_cta": "<1-2 sentences: quick 'why me' punch, then direct ask for a call. MUST ask for time explicitly.>"
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
        user_msg += "\n━━ COMPANY INTELLIGENCE (use this to write a genuinely human email) ━━\n"

        # The single most important thing: a real quote or human moment from the JD
        if jd_insights.get("memorable_quote"):
            user_msg += f"\nMEMORABLE QUOTE FROM THEIR JD (use this to open — quote it or reference it specifically, this proves you actually read it):\n\"{jd_insights['memorable_quote']}\"\n"
        if jd_insights.get("mission_hook"):
            user_msg += f"Why their mission matters: {jd_insights['mission_hook']}\n"

        if jd_insights.get("their_world"):
            user_msg += f"\nWhat they're building and why it's hard: {jd_insights['their_world']}\n"
        if jd_insights.get("seen_moment"):
            user_msg += f"The observation that makes them feel understood: {jd_insights['seen_moment']}\n"
        if jd_insights.get("their_hard_problem"):
            user_msg += f"The core challenge this role solves: {jd_insights['their_hard_problem']}\n"

        # Experience gap — acknowledge it honestly
        if jd_insights.get("experience_gap"):
            user_msg += "\nEXPERIENCE GAP: This role asks for more experience than the candidate has. Acknowledge it honestly in ONE sentence ('I know you're looking for X — I won't pretend I have that.') then immediately pivot to what matters. Do NOT avoid the gap. Honesty makes the rest of the email more credible.\n"

        match_quality = jd_insights.get("match_quality", "strong")
        lead = jd_insights.get("lead_projects", [])
        if match_quality == "weak":
            builder_angle = jd_insights.get("builder_angle", "Solo-shipped multiple production tools with full ownership.")
            user_msg += f"\nMATCH QUALITY: WEAK. Do NOT force a project to fit. Lead with the builder story: {builder_angle}\n"
            user_msg += "Reference projects briefly as evidence of range, not as direct parallels.\n"
            if lead:
                user_msg += f"Projects to reference (describe honestly): {', '.join(lead)}\n"
        elif lead:
            user_msg += f"\nPROJECT TO BUILD THE EMAIL AROUND: {', '.join(lead)}\n"
            if jd_insights.get("lead_reason"):
                user_msg += f"Why it fits: {jd_insights['lead_reason']}\n"
            user_msg += "Go deep on one decision or insight from this project — not a summary, a story.\n"

        if jd_insights.get("human_cta"):
            user_msg += f"\nCTA: {jd_insights['human_cta']}\n"
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
        word_limit = 150
        user_msg += f"\nDraft the cold email now. Output ONLY: Subject: line, then body. Nothing else. No greeting. No links. No sign-off. No separator lines. No em dashes. NO BULLET POINTS — full prose paragraphs only. Subject: 60 chars MAX. Body: {word_limit} words HARD MAX (count before output — if over {word_limit}, delete the weakest sentence). First word of the email MUST be about them, not 'I'. ONE project only — go deep, not wide."
        user_msg += "\n\nCRITICAL — THE LAST SENTENCE MUST ask for a call or time. Budget: open with their world (2-3 sentences referencing something specific from their JD) + honest bridge to your work (1-2 sentences) + one proof story (2-3 sentences) + CTA (1-2 sentences). The CTA is NON-NEGOTIABLE. If running out of words, cut a proof sentence — never cut the CTA. Examples: 'Worth a quick call this week?' or 'Would love 20 minutes if you're open to it.' DO NOT end without asking for time."

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
    max_words = 100 if is_enterprise else 160
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

    # CTA safety net — if the email doesn't end with an ask, append one
    cta_signals = ["call", "chat", "talk", "minutes", "interview", "resume attached", "meet", "connect", "conversation", "open to", "worth a"]
    last_sentence = body.rsplit(".", 1)[-1].lower() + body.rsplit("?", 1)[-1].lower()
    has_cta = any(sig in last_sentence for sig in cta_signals)
    if not has_cta:
        if is_enterprise:
            body = body.rstrip(".") + ". I'd welcome the chance to interview for this role. Resume is attached."
        else:
            body = body.rstrip(".") + ". Worth a quick call this week?"
        print(f"[Email] CTA was missing — appended fallback CTA")

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
