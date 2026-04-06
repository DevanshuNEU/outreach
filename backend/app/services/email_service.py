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
If the job clearly asks for more experience than the candidate has, acknowledge it — but from a position of strength, NOT defense.

WRONG (sounds desperate):
"I know you're looking for 5 years — I won't pretend I have that. But..."
"I won't claim I've built X before. But I've built..."
"I don't have experience with X, but..."

These put the reader in judge mode. They're already thinking "no."

RIGHT (confident, honest, forward-leaning):
Acknowledge what you bring first. Then state the gap in a single sentence that reframes it as a specific choice rather than a deficit. Then pivot immediately to what matters.

Example: "Two years in, not five. But those two years were in production under real load, debugging problems that didn't show up in staging. That's the instinct this role needs."

The goal: make the reader think "this person knows what they're doing AND they're being straight with me" — not "this person is trying to convince me to overlook their resume."

━━ HOW TO PROVE YOUR WORTH ━━
ONE story. The single most relevant project or moment. Go deep on the decision and outcome — not a summary, a story. The architecture choice that changed everything. The insight that unlocked the result. Not: "I built a RAG system that improved accuracy." Instead: "The insight was that chunking strategy mattered more than model choice. One change to how we split code at AST boundaries beat every model upgrade we tried combined."

Do NOT list multiple projects. One deep story beats five shallow mentions.

━━ HOW TO CLOSE ━━
A direct ask for time. Not a question about their work. Not "let me know." A direct ask: "Worth a quick call this week?" or "Open for 20 minutes this week?"

NOTE: Graduation date and work authorization are already in the sign-off block appended after the body — do NOT repeat them in the body. The reader will see them.

The reader must finish the email knowing exactly what you want: a conversation. The ball is in their court.

━━ THE "SO WHAT?" TEST ━━
Every sentence must survive: if the reader thinks "so what?" after reading it, cut it or rewrite it. "I'm a software engineer" fails. "I brought p95 from 800ms to 280ms before anyone suggested adding servers" passes.

━━ SUBJECT LINES ━━
The subject line has ONE job: make them open the email. It creates a curiosity gap.

ANTI-PATTERNS (these get deleted, not read):
- Never restate their own JD language back at them ("seamlessly woven into customer workflows" — that's their words, not a hook)
- Never use the company name — they know who they are
- Never describe what you're doing ("following up", "interested in role", "quick note")
- Never be vague ("a quick question", "something interesting")

PATTERNS THAT WORK:
- A specific pain point as a statement: "voice agents failing to respond in 100ms"
- A tension or gap: "the gap between demo and production deployment"
- A counter-intuitive insight: "it wasn't the model. it was the chunking"
- Something that only applies to THIS company: "your kafka consumer lag at 50k TPS"
- A problem they publicly have: "what breaks first when robots leave the lab"

TEST: Read the subject line and ask "would someone who works there think this person knows something I don't?" If yes, use it. If it could apply to any company, rewrite it.

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


FOLLOWUP_PROMPT = """You write short follow-up emails for cold outreach. The initial email has already been sent. These are bumps — short, human, not pushy.

RULES:
- ZERO em dashes. ZERO bullet points. ZERO emojis.
- No "just following up" or "circling back" or "wanted to check in" — those get deleted.
- Each follow-up must feel different from the last. New angle, new energy.
- Short sentences. Conversational. Like a real person bumping a thread.
- NO greeting (Hi/Hey) — just the body. Greeting is added separately.
- NO sign-off — added separately.
- NEVER invent metrics or numbers not in the context provided.

FU1 (day 3 — first bump):
- 2-3 sentences MAX. Under 40 words.
- Reference the topic of the original email (not "my previous email").
- One small new observation or hook — something you noticed about their product/company, or a tiny new angle on your story.
- End with a direct ask: "Worth a quick call?" or "Still open for 15 minutes?"

FU2 (day 10 — second bump):
- 2 sentences MAX. Under 30 words.
- Even more direct. Less explanation.
- New angle if possible — a recent result, a thing you noticed, or just genuine persistence.
- End with the ask.

FU3 (day 17 — last touch):
- 2 sentences MAX. Under 25 words.
- Gracious. Make it easy to say no. "If the timing's off, no worries" energy.
- Still ends with a question, not a statement.

Output ONLY the body text for the requested follow-up number. No label. No greeting. No sign-off."""


def generate_followups(
    client: anthropic.Anthropic,
    company_name: str,
    job_title: str | None,
    email_subject: str,
    email_body: str,
    model: str = "claude-haiku-4-5-20251001",
) -> dict[str, str]:
    """Generate FU1, FU2, FU3 drafts based on the initial email. Returns dict with fu1/fu2/fu3 keys."""
    context = f"""Company: {company_name}
Role: {job_title or "Software Engineer"}
Original subject: {email_subject}
Original email body:
{email_body[:600]}"""

    results = {}
    fu_specs = [
        ("fu1", "Write FU1 (day 3 follow-up). Under 40 words. Body only."),
        ("fu2", "Write FU2 (day 10 follow-up). Under 30 words. Body only."),
        ("fu3", "Write FU3 (day 17 follow-up). Under 25 words. Body only."),
    ]

    for key, instruction in fu_specs:
        try:
            r = client.messages.create(
                model=model,
                max_tokens=150,
                system=FOLLOWUP_PROMPT,
                messages=[{"role": "user", "content": f"{context}\n\n{instruction}"}],
            )
            text = r.content[0].text.strip().strip('"')
            # Kill any em dashes that slip through
            text = re.sub(r'\s*[—–]\s*([a-zA-Z])', lambda m: '. ' + m.group(1).upper(), text)
            text = re.sub(r'\s*[—–]\s*', '. ', text)
            results[key] = text
        except Exception:
            results[key] = ""

    return results


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


EMAIL_VALIDATION_PROMPT = """You are a brutally honest cold email reviewer. Your job is to find problems, not validate choices. Be hard on the email. If something is weak, say it clearly.

Review the email and return ONLY valid JSON:
{
  "score": <integer 1-10>,
  "subject_verdict": "<'strong' or 'weak'>",
  "subject_reason": "<one sentence: why strong or weak>",
  "proof_verdict": "<'strong' or 'weak'>",
  "proof_reason": "<one sentence: does the proof point actually match what this role needs?>",
  "has_cta": <true or false>,
  "has_fragments": <true or false>,
  "has_em_dashes": <true or false>,
  "has_bullets": <true or false>,
  "word_count": <integer>,
  "issues": ["<specific problem 1>", "<specific problem 2>"],
  "strengths": ["<what actually works 1>"]
}

SCORING:
9-10: Reads like a real human wrote it. Specific quote or hook from their world. Honest gap acknowledgment. Proof matches role perfectly. Ends with a question. No fragments.
7-8: Good but one clear weakness (subject is generic OR proof doesn't perfectly match role OR slightly over word limit).
5-6: Decent bones but feels templated. Wrong proof point, or subject just restates their JD, or missing gap acknowledgment.
3-4: Multiple problems. Generic, wrong proof, no hook, reads like a mass blast.
1-2: Spam. Could be sent to any company. No specificity, no honesty.

SUBJECT VERDICT — weak if:
- It uses the company's own JD language back at them
- It could apply to any company in the industry
- It describes what you're doing ("following up", "interested in role")
- It's a statement with no hook (just a product feature name)

Strong if:
- It would make someone at this company think "how does this person know that?"
- It references a specific pain point, tension, or insight about THIS company

PROOF VERDICT — weak if:
- The proof story doesn't map to the core challenge of this specific role
- For a customer-facing/FDE role: backend API story is weak (devOS/user-behavior story is strong)
- For a backend/infra role: portfolio OS story is weak (API latency story is strong)
- For an AI/ML role: infrastructure story is weak (retrieval/chunking story is strong)

ISSUES — be specific. Not "the email could be better." Say exactly what is wrong:
- "Subject line 'seamlessly woven into customer workflows' is just their JD language restated — creates zero curiosity"
- "Proof point is a backend API story but this is a Forward-Deployed Engineer role — devOS user-behavior story would match better"
- "Last sentence 'But product-minded engineering...' is a fragment — has no verb"
- "Word count is 162, over the 150 limit"

Return ONLY the JSON. No explanation outside it."""


def _validate_email(
    client: anthropic.Anthropic,
    subject: str,
    body: str,
    job_description: str,
    template_slug: str,
) -> dict:
    """Self-validate the generated email. Returns score + issues so user knows what's weak."""
    try:
        msg = f"""Template type: {template_slug}
Subject: {subject}
Body:
{body}

Job Description (first 1500 chars):
{job_description[:1500] if job_description else "Not provided"}"""

        r = client.messages.create(
            model="claude-haiku-4-5-20251001",
            max_tokens=600,
            system=EMAIL_VALIDATION_PROMPT,
            messages=[{"role": "user", "content": msg}],
        )
        raw = r.content[0].text.strip()
        if raw.startswith("```"):
            raw = raw.split("```")[1]
            if raw.startswith("json"):
                raw = raw[4:]
        result = json.loads(raw.strip())
        print(f"[Validation] score={result.get('score')}/10 issues={result.get('issues')}")
        return result
    except Exception as e:
        print(f"[Validation] failed: {e}")
        return {"score": None, "issues": [], "strengths": []}


# Role type → best proof point hint
ROLE_PROOF_HINTS = {
    "fde": "For a Forward-Deployed Engineer role, the BEST proof point is the devOS portfolio (user behavior analysis → engineered outcome → 4+ min sessions). This proves customer/user obsession better than any backend story. Use it if available.",
    "fullstack": "For full-stack roles, lead with devOS (shows product thinking + full ownership) then connect to OpenCodeIntel scale.",
    "ai-ml": "For AI/ML roles, OpenCodeIntel AST chunking insight is the primary story. Everything else is secondary.",
    "rag": "For RAG/retrieval roles, OpenCodeIntel retrieval pipeline is the ONLY story. Go deep on the eval framework and chunking insight.",
    "context": "For context engineering roles, OpenCodeIntel is the primary story. The insight: chunking > model choice.",
    "backend": "For backend roles, the production API platform story (p95 800ms→280ms, profiling first) is strongest. SecureScale is secondary.",
    "cloud": "For cloud/devops/SRE roles, SecureScale (multi-AZ Terraform, CloudWatch, provisioning 2hrs→10min) is primary. TA curriculum is secondary.",
    "swe": "For general SWE roles, match the proof point to the company's primary challenge. Default to OpenCodeIntel if uncertain.",
}


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
Suggest a CTA that feels natural and direct. A direct ask for time: "Worth a quick call this week?" or "Open for 20 minutes this week?" — not "let me know" or "would love to connect." NOTE: graduation date and work authorization are already in the sign-off block — do NOT repeat them in the CTA.

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
  "human_cta": "<1-2 sentences: direct ask for time. Example: 'Worth a quick call this week?' — availability info is already in the sign-off, do not repeat it here>"
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
    template_slug: str = "swe",
    model: str = "claude-haiku-4-5-20251001",
    previous_subject: str | None = None,
    previous_body: str | None = None,
    previous_issues: list[str] | None = None,
) -> dict:
    client = anthropic.Anthropic(api_key=settings.anthropic_api_key)
    print(f"[Email] using model={model}")

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

    # Inject role-type proof point hint
    if not is_enterprise and template_slug in ROLE_PROOF_HINTS:
        user_msg += f"\n━━ ROLE TYPE PROOF HINT ━━\n{ROLE_PROOF_HINTS[template_slug]}\n"

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

        # Experience gap — acknowledge from strength, not defense
        if jd_insights.get("experience_gap"):
            user_msg += "\nEXPERIENCE GAP: This role asks for more experience than the candidate has. Acknowledge it — but lead with what you bring first. State the gap in ONE sentence that reframes it as a specific fact, not an apology. Then pivot immediately. NEVER use 'I won't pretend', 'I won't claim', or 'I don't have X but'. Those phrases put the reader in judge mode. Instead: state what you DO have confidently, then acknowledge the gap as a single honest sentence, then move forward. Example pattern: 'Two years in production, not five. But those two years were [specific context that makes them dense/valuable].' The gap acknowledgment should make the reader think 'honest and self-aware' not 'trying to get around their requirements'.\n"

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

    # Revision mode: show previous draft + specific issues to fix
    if previous_issues and previous_body:
        user_msg += "\n━━ REVISION REQUEST ━━\n"
        user_msg += "This is a REVISION. A previous version was generated and reviewed. Here is the previous draft and its specific problems.\n\n"
        if previous_subject:
            user_msg += f"Previous subject: {previous_subject}\n"
        user_msg += f"Previous body:\n{previous_body}\n\n"
        user_msg += "ISSUES IDENTIFIED IN THE PREVIOUS VERSION (fix ALL of these):\n"
        for i, issue in enumerate(previous_issues, 1):
            user_msg += f"{i}. {issue}\n"
        user_msg += "\nWrite a NEW version that fixes every issue above. Do not just patch the old email — rewrite it with the fixes baked in naturally. The new version should be noticeably better.\n"
        user_msg += "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"

    if is_enterprise:
        word_limit = 100
        user_msg += f"\nDraft the email now. Output ONLY: Subject: line, then body. Nothing else. No greeting. No links. No sign-off. No separator lines. No em dashes. Subject format: 'MS SWE May 2026 . [Role] . STEM OPT, no sponsorship needed' (under 70 chars). Body: {word_limit} words HARD MAX. First word MUST be about the company or role, not 'I'."
        user_msg += "\n\nCRITICAL — THE LAST SENTENCE OF THE BODY MUST ask for an interview. Examples: 'I'd love the opportunity to interview for this role. Resume is attached.' or 'Would welcome the chance to interview. Resume attached.' DO NOT end the email without explicitly asking for an interview and mentioning resume attached."
    else:
        word_limit = 150
        user_msg += f"\nDraft the cold email now. Output ONLY: Subject: line, then body. Nothing else. No greeting. No links. No sign-off. No separator lines. No em dashes. NO BULLET POINTS — full prose paragraphs only. Subject: 60 chars MAX. Body: {word_limit} words HARD MAX (count before output — if over {word_limit}, delete the weakest sentence). First word of the email MUST be about them, not 'I'. ONE project only — go deep, not wide."
        user_msg += "\n\nEVERY SENTENCE MUST BE GRAMMATICALLY COMPLETE. No fragments. 'But product-minded engineering and the ability to...' is a fragment — it has no verb and makes no sense alone. Every sentence needs a subject and a verb. Read each sentence before outputting it."
        user_msg += "\n\nTHE LAST LINE MUST BE A QUESTION ASKING FOR A CALL. Not a statement. Not a fragment. A complete question. Examples: 'Worth a quick call this week?' or 'Open for 20 minutes this week?' Cut any proof sentence to make room. Never skip this."

    response = client.messages.create(
        model=model,
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

    # Kill em dashes — replace with period and capitalize the next word
    body = re.sub(r'\s*[—–]\s*([a-zA-Z])', lambda m: '. ' + m.group(1).upper(), body)
    body = re.sub(r'\s*[—–]\s*', '. ', body)  # catch any remaining
    body = re.sub(r'\.\s+\.', '.', body)       # clean up double periods
    subject = re.sub(r'\s*[—–]\s*', ': ', subject)

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
    cta_signals = ["call", "chat", "talk", "minutes", "interview", "resume attached", "meet", "connect", "conversation", "open to", "worth a", "quick chat", "15 min", "20 min", "this week", "your time"]
    # Check last TWO sentences to catch things like "That's why I'm drawn to your team."
    last_part = body.rsplit(".", 2)[-2:]
    last_part_text = " ".join(last_part).lower() + body.rsplit("?", 1)[-1].lower()
    has_cta = any(sig in last_part_text for sig in cta_signals)
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
    # Haiku: $1/M input, $5/M output | Sonnet: $3/M input, $15/M output
    if "sonnet" in model:
        cost_cents = (input_tokens * 0.0003 + output_tokens * 0.0015)
    else:
        cost_cents = (input_tokens * 0.0001 + output_tokens * 0.0005)

    db.table("api_usage").insert({
        "user_id": user_id,
        "service": "anthropic",
        "endpoint": "email_draft",
        "tokens_in": input_tokens,
        "tokens_out": output_tokens,
        "estimated_cost_cents": round(cost_cents, 4),
    }).execute()

    # Self-validate — AI critiques its own output so user knows what's weak
    validation = {}
    if not is_enterprise and job_description:
        validation = _validate_email(client, subject, body, job_description, template_slug)

    # Generate follow-up drafts (always use Haiku — these are short bumps, no need for Sonnet)
    followups = {}
    if not is_enterprise:
        followups = generate_followups(
            client=client,
            company_name=company_name,
            job_title=None,
            email_subject=subject,
            email_body=body,
            model="claude-haiku-4-5-20251001",
        )

    return {
        "subject": subject,
        "body": body,
        "linkedin_note": linkedin_note,
        "followup_1_body": followups.get("fu1", ""),
        "followup_2_body": followups.get("fu2", ""),
        "followup_3_body": followups.get("fu3", ""),
        "quality": {
            "score": validation.get("score"),
            "issues": validation.get("issues", []),
            "strengths": validation.get("strengths", []),
            "subject_verdict": validation.get("subject_verdict"),
            "subject_reason": validation.get("subject_reason"),
            "proof_verdict": validation.get("proof_verdict"),
            "proof_reason": validation.get("proof_reason"),
            "has_cta": validation.get("has_cta", True),
            "has_fragments": validation.get("has_fragments", False),
        }
    }
