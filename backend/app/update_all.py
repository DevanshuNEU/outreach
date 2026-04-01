"""
Rebuild Devanshu's profile + all 8 role templates with deep psychological hooks.
Run: python -m app.update_all
"""
import uuid
from app.database import get_db

DEVANSHU_USER_ID = "193871f2-996c-49fa-9222-402bc3621cb0"

# ── Profile ─────────────────────────────────────────────────────────────────

BACKGROUND = """MS Software Engineering Systems, Northeastern University (GPA 3.85, May 2026). BTech in ICT, DAIICT India (2022).

2 years of industry experience as a full-stack/backend engineer at Jaksh Enterprise (Aug 2022 - Jul 2024), followed by MS and independent projects.

Before grad school I spent 2 years as a full-stack/backend engineer at a production e-commerce company. I owned a RESTful API platform handling 15K+ daily requests and 12K+ monthly active users. I didn't add servers when latency spiked. I profiled first. Found three root causes: missing async event queues, no B-tree indexes on the hot PostgreSQL queries, no Redis caching layer. p95 dropped 65%, from 800ms to 280ms. Checkout completion up 18% during peak traffic. Auth middleware and rate limiting drove a 35% conversion lift. Built zero-downtime CI/CD with GitHub Actions and Docker. Compressed sprint releases from 2 weeks to 3 days, 99.5% deployment success rate.

The OpenCodeIntel insight: chunking strategy moved retrieval accuracy more than any model swap. AST parsing across 8 languages vs. naive token splitting. Naive splitting destroys function boundaries, class relationships, import chains. Tree-sitter preserves all of it. That one architectural decision outperformed every embedding model upgrade combined. Built the eval framework first (Hit@1, Hit@3, MRR per layer) before touching any optimization. 87.5% Hit@1. 681 commits. MCP server integrates natively with Cursor and Windsurf.

Saar: CLI tool that analyzes any codebase and auto-generates CLAUDE.md, .cursorrules, copilot-instructions. Detects naming conventions, auth patterns, custom exception hierarchies. Research-backed output length (~100 lines) because longer context files actually reduce AI task success rates. Used with Claude Code, Cursor, Copilot.

LCO (Local Context Optimizer): Chrome extension that intercepts Claude's API stream in-browser. Real-time token counting using the same BPE tokenizer Claude uses. Per-message and session cost estimation for Opus, Sonnet, Haiku. Context window bar. Zero data leaves the machine. TypeScript. In production.

devOS: my portfolio is a full macOS-style OS in the browser. Window management, file system, app launcher, Terminal with CLI commands (including `hire devanshu`), Arcade, Finder that browses my GitHub repos live. Not a flex. I analyzed that portfolios bounce in 8 seconds. An OS forces you to explore. It's a trap. It works. Next.js 15, Framer Motion, Zustand, Express backend.

Graduate TA for Cloud Computing at Northeastern. Wrote the Docker, GitHub Actions, and Terraform curriculum across 3 sections, 180+ students. Teaching infrastructure forces understanding you can't fake.

F1 visa. OPT then STEM OPT. 3 years work authorization. No H1B lottery needed."""

PROJECTS = [
    {
        "name": "OpenCodeIntel",
        "description": "Open-source AI code intelligence platform. Semantic code search by meaning, not keywords — search 'where we handle payments' and get the right code even without knowing function names. Hybrid RAG pipeline: pure vector (~70%) → BM25+vector (~80%) → Cohere reranking (87.5% Hit@1). The counterintuitive insight: Tree-sitter AST chunking across 8 languages moved accuracy more than every model swap combined. Naive token splitting destroys function boundaries and import chains. AST preserves them. Built eval framework (Hit@1, Hit@3, MRR per layer) before any optimization. MCP server with 6 semantic tools (code search, dependency graphs, impact analysis, codebase DNA) integrates natively with Cursor and Windsurf. WebGL dependency visualization via Sigma.js + ForceAtlas2. One-click GitHub OAuth import. TypeScript + Python, Pinecone, Supabase, pgvector, GitHub Actions CI/CD.",
        "metrics": "87.5% Hit@1, 681 commits, 12 stars, live at opencodeintel.com",
        "url": "https://opencodeintel.com"
    },
    {
        "name": "LCO (Local Context Optimizer)",
        "description": "Chrome extension that gives you real-time visibility into Claude's token usage and costs. Problem: Claude's web UI strips token counts entirely. LCO fixes this without a backend. Technical architecture: three-world isolation model (MAIN world injects into window.fetch, content script renders a closed Shadow DOM overlay, service worker handles token counting and storage). Intercepts SSE streams using window.fetch.tee() so Claude's UI is never disrupted. Token counting: real-time character approximation during streaming, then final BPE count using js-tiktoken with Anthropic's actual claude.json vocabulary (20-40ms). 5-layer message validation (origin, source, namespace, session UUID, schema) between worlds. Per-message and session cost tracking for Opus/Sonnet/Haiku. Zero data persists — chrome.storage.session only. TypeScript, Bun, WXT, Manifest V3.",
        "metrics": "48 commits, privacy-first, zero backend, all processing in-browser",
        "url": "https://github.com/OpenCodeIntel/lco"
    },
    {
        "name": "Saar",
        "description": "CLI tool (pip install saar) that deep-analyzes any codebase and auto-generates CLAUDE.md, AGENTS.md, .cursorrules, copilot-instructions.md. Because AI agents need structured context, not raw code dumps. Detects: package managers (bun/pnpm/npm/yarn), logging libraries, auth patterns and decorators, custom exception hierarchies (caught 218 custom exceptions in one real project), naming conventions, critical files. Research-backed output: ~100 lines default because longer context files reduce AI task success rates. saar diff tracks changes since last analysis. saar lint catches redundancy. saar check integrates into CI. Works with Claude Code, Cursor, Copilot, Gemini CLI. Python. Runs entirely locally.",
        "metrics": "pip installable, works with all major AI coding tools",
        "url": "https://github.com/OpenCodeIntel/saar"
    },
    {
        "name": "devOS (Portfolio)",
        "description": "Full macOS-style operating system in the browser. Window management, file system, app launcher — all from scratch. Includes: Terminal with real CLI commands (try: hire devanshu), Finder that browses GitHub repos live, Arcade with interactive games, Skill Tree visualizing technical expertise, Analytics with transparent visitor tracking, Changelog. Not a flex. I analyzed recruiter behavior: portfolios bounce in 8 seconds. An OS forces you to click around. It's a trap. It works. Next.js 15, TypeScript, Tailwind CSS, Framer Motion, Zustand. Express + Prisma + SQLite backend. Deployed on Vercel.",
        "metrics": "Full OS in browser, multiple interactive apps, live on devanshuchicholikar.com",
        "url": "https://devanshuchicholikar.com"
    },
    {
        "name": "Production API Platform (2 years industry experience)",
        "description": "Full-stack/backend engineer at a production e-commerce company for 2 years (Aug 2022 - Jul 2024). Owned a RESTful API platform serving 15K+ daily requests and 12K+ monthly users. When p95 latency spiked, I profiled before touching anything. Found three root causes: missing async event queues, unindexed hot PostgreSQL queries, no Redis caching. Fixed all three. p95 dropped 65% (800ms to 280ms). Checkout completion up 18% during peak traffic. Built auth middleware and rate limiting that drove 35% conversion lift. Replaced a 2-week sprint cycle with zero-downtime CI/CD via GitHub Actions and Docker — releases went from 2 weeks to 3 days, 99.5% deployment success rate. Node.js, Express, PostgreSQL, Redis, Docker, GitHub Actions.",
        "metrics": "p95 800ms to 280ms (-65%), checkout +18%, conversion +35%, releases 2 weeks to 3 days, 99.5% deploy success, 15K+ daily requests",
        "url": None
    },
    {
        "name": "SecureScale",
        "description": "Production-grade multi-AZ AWS infrastructure via modular Terraform. Defense-in-depth security: 4 KMS encryption keys, IAM least-privilege, NAT isolation. Zero-downtime CI/CD with immutable Packer AMI builds (30-second boot). CloudWatch + SNS observability stack.",
        "metrics": "Provisioning: 2hrs to 10min, cloud spend -30%",
        "url": None
    },
    {
        "name": "Graduate TA, Cloud Computing, Northeastern",
        "description": "Wrote the lab curriculum for Docker, GitHub Actions, and Terraform at Northeastern. Used across 3 sections, 180+ students. Leads system design reviews for 15 teams. Teaching infrastructure forces you to understand it at a level you cannot fake.",
        "metrics": "180+ students, 3 sections, 15 teams reviewed",
        "url": None
    }
]

SIGN_OFF = """Best,
Devanshu Chicholikar
MS Software Engineering, Northeastern, May 2026
3 years work authorization (STEM OPT). No H1B needed.
devanshuchicholikar.me | github.com/OpenCodeIntel"""

LINKS_BLOCK = """opencodeintel.com
github.com/OpenCodeIntel/opencodeintel
devanshuchicholikar.me"""

# ── Templates ────────────────────────────────────────────────────────────────

TEMPLATES = [
    # ── 1. SOFTWARE ENGINEER ─────────────────────────────────────────────────
    {
        "slug": "swe",
        "title": "Software Engineer",
        "color": "#3b82f6",
        "tagline": "Eval framework first. 681 commits later. Numbers moved.",
        "sort_order": 0,
        "role_prompt_addition": """ROLE: Software Engineer (backend-leaning or full-stack)
PSYCHOLOGICAL FRAME: The engineer who measures before touching anything. Most don't. That discipline shows in every system built. Lead with the eval-first mindset, not credentials.

SUBJECT LINE, pick the most specific to the company:
"What actually moved retrieval accuracy (eval framework first)"
"681 commits. Measured every step. Here's what moved."
"Profiled before touching a server. p95 800ms → 280ms. Checkout +18%."
Or: write one referencing a specific engineering decision, tech choice, or post the company has made.

HOOK (1-2 sentences): Research the company. One specific thing: a product decision, a blog post, a scale challenge they've talked about publicly. If another company name could slot in, it's not specific enough. Rewrite until it can't.

CONNECTION (use this story, adapt company context):
"I built the eval framework for OpenCodeIntel before touching any optimization. Hit@1, Hit@3, MRR at each retrieval layer. Then I ran three measured iterations: pure vector (~70%), add BM25 (~80%), Cohere reranking (87.5% Hit@1). The biggest accuracy jump didn't come from any of that. It came from switching how I chunked code. Naive token splitting destroys function boundaries, import chains, class hierarchy. Tree-sitter AST parsing across 8 languages preserves all of it. One architectural decision outperformed every model swap combined. That's the discipline: measure first, touch second. 681 commits, MCP server live in Cursor and Windsurf, opencodeintel.com."

BULLETS, pick 3 that map best to this company's work:
"Eval framework before touching the pipeline: Hit@1, Hit@3, MRR per layer. Can't improve what you haven't isolated."
"AST chunking across 8 languages. Biggest accuracy gain. Beat every model swap."
"MCP server with 6 semantic tools. Integrates with Cursor and Windsurf. 681 commits. Open source."
"E-commerce API: profiled before adding servers. Found 3 root causes. p95 800ms → 280ms. Checkout conversion +18%."
"LCO: Chrome extension intercepting Claude's SSE stream with window.fetch.tee(). Zero backend. Real-time BPE token counting. 3-world isolation architecture."
"SecureScale: provisioning from 2 hours to 10 minutes. Cloud spend down 30%."

CTA: "15 minutes to talk shop?" or "Worth a 15-minute call?" Casual, equal-footing.

HARD LIMITS: Under 130 words in the body. Zero em dashes. No "passionate." No "I believe I'd be a great fit." Start with the hook, not with yourself.""",
        "example_email": """Subject: What actually moved retrieval accuracy (eval framework first)

Hey [Name],

[1-2 sentences specific to this company's engineering, a product decision, scale challenge, or tech post they've published. Cannot apply to any other company.]

I built the eval framework before touching any optimization. Hit@1, Hit@3, MRR at each retrieval layer of OpenCodeIntel. Then three measured iterations: pure vector (~70%), add BM25 (~80%), Cohere reranking (87.5% Hit@1). The biggest jump came from switching how I chunked code, not from any model change. Naive token splitting destroys function boundaries. Tree-sitter AST parsing across 8 languages preserves them. That one decision outperformed every model swap combined.

Same discipline in LCO: intercepting Claude's SSE stream with window.fetch.tee(), real BPE tokenizer, three-world isolation. Measure and understand the system before touching it.

What I shipped:
* Eval framework first. Isolated each layer before optimizing any of it.
* AST chunking across 8 languages. Biggest accuracy gain in the pipeline.
* MCP server with 6 semantic tools. Cursor and Windsurf. 681 commits. Live.

15 minutes to talk shop?"""
    },

    # ── 2. AI/ML ENGINEER ────────────────────────────────────────────────────
    {
        "slug": "ai-ml",
        "title": "AI/ML Engineer",
        "color": "#8b5cf6",
        "tagline": "Most people swap the model. You found out that's not where accuracy lives.",
        "sort_order": 1,
        "role_prompt_addition": """ROLE: AI/ML Engineer
PSYCHOLOGICAL FRAME: Peer-to-peer technical conversation. You're not applying. You're comparing notes. Lead with the counterintuitive insight, not credentials.

SUBJECT LINE:
"What actually moved RAG accuracy (it wasn't the model)"
"The chunking decision that beat every embedding model upgrade"
Or: something referencing their specific AI architecture, retrieval approach, or a technical post they've published.

HOOK (1-2 sentences): Their AI product: a specific model they use, a retrieval challenge in their product, a technical blog post. Show you've actually looked at what they're building, not just the job description.

THE INSIGHT TO LEAD WITH:
"Everyone optimizes the embedding model. That's not where accuracy lives. I spent a year on OpenCodeIntel's retrieval pipeline and the single decision that moved accuracy more than anything else was how I chunked the code. Not which model I used. Naive token splitting destroys function boundaries, class relationships, import chains. Tree-sitter AST parsing across 8 languages preserves all of it. That one change outperformed every model swap combined."

ITERATION STORY: Three measured iterations. Pure vector: ~70%. Add BM25: ~80%. Cohere reranking: 87.5% Hit@1. But emphasize: built the eval framework (Hit@1, Hit@3, MRR) before touching any of it. Most teams ship and guess.

BULLETS, pick 3:
"AST chunking across 8 languages. Biggest accuracy gain in the pipeline. Not the model."
"Custom eval framework: Hit@1, Hit@3, MRR. Isolated each layer's contribution before optimizing."
"Saar: auto-generates CLAUDE.md and .cursorrules from deep static analysis. Context quality is the actual RAG bottleneck."
"MCP server with 6 semantic tools. Integrates with Cursor and Windsurf. 681 commits. opencodeintel.com is live."

CTA: "15 minutes to compare notes on retrieval?" Peer conversation, not job pitch.

DO NOT: Explain what RAG is. They know. Don't say "passionate about AI." Skip credentials in the body. The sign-off handles that. Go straight to the architecture insight.""",
        "example_email": """Subject: What actually moved RAG accuracy (it wasn't the model)

Hey [Name],

[1-2 sentences about their specific AI product, retrieval approach, or a technical post they've published. Something that shows you actually looked at what they're building.]

Everyone optimizes the embedding model. That's not where accuracy lives.

I spent a year on OpenCodeIntel's retrieval pipeline. Three measured iterations: pure vector (~70%), add BM25 (~80%), Cohere reranking (87.5% Hit@1). But the single biggest jump came from switching how I chunked code, not from any model change. Naive token splitting destroys semantic boundaries. Tree-sitter AST parsing across 8 languages preserves function relationships, import chains, class hierarchy. That one architectural decision outperformed every model upgrade combined. Built the eval framework first: Hit@1, Hit@3, MRR per layer. Most teams ship and guess.

What I shipped:
* AST chunking across 8 languages. Single biggest accuracy gain. Not the embedding model.
* Saar: auto-generates CLAUDE.md from static analysis. Context quality is the actual bottleneck.
* 681 commits. MCP server that integrates with Cursor and Windsurf. opencodeintel.com is live.

15 minutes to compare notes on retrieval?"""
    },

    # ── 3. FORWARD-DEPLOYED ENGINEER ─────────────────────────────────────────
    {
        "slug": "fde",
        "title": "Forward-Deployed Engineer",
        "color": "#f59e0b",
        "tagline": "Demos work in controlled conditions. Tools people trust survive the actual workflow.",
        "sort_order": 2,
        "role_prompt_addition": """ROLE: Forward-Deployed / Solutions Engineer
PSYCHOLOGICAL FRAME: You understand users at a level most engineers skip. You start with what the user actually does, then build backwards. And you have receipts: real deployments, real workflows, real users.

SUBJECT LINE:
"The gap between a demo and a tool people trust"
"Built it for real users. Here's what I learned."
Or: something referencing their specific customer deployment challenge, integration complexity, or a post about their go-to-market motion.

HOOK (1-2 sentences): How they deploy AI to customers, what their integration story looks like, or a specific friction point their users face. Something concrete you found by actually looking.

THE TWO STORIES TO USE:
Story 1, MCP server: "OpenCodeIntel's MCP server has 6 semantic tools: code search, dependency graphs, impact analysis, codebase DNA. Built to integrate natively with Cursor and Windsurf. Not a prototype. A tool they rely on in their actual development workflow."
Story 2, Portfolio OS: "My portfolio is a full OS in the browser. Not a flex. I analyzed recruiter behavior. Portfolios bounce in 8 seconds. So I built something that forces you to click around. Average session: 4+ minutes. I started with the user's behavior, then engineered the outcome I wanted. That's how I approach every deployment."

USE ONE OR BOTH depending on what maps to the company.

BULLETS, pick 3:
"MCP server with 6 semantic tools. Engineers call it in Cursor and Windsurf on real codebases. 681 commits."
"Portfolio OS: analyzed recruiter bounce behavior, built a trap. Average session 4+ minutes vs 8-second bounce. User problem first."
"Saar: turns any repo into context an AI agent can actually use. Auto-generates CLAUDE.md, .cursorrules from static analysis."
"LCO: users couldn't see token costs in Claude's UI. Built the interception layer in-browser. Zero backend. SSE stream, BPE tokenizer, Shadow DOM overlay. Started with the real friction."

CTA: "15 minutes to talk about deploying AI where it holds up?" or "Worth a quick call this week?"

DO NOT: Use "bridge the gap." Don't list tools without showing what user problem they solved. Every bullet has a user and an outcome.""",
        "example_email": """Subject: The gap between a demo and a tool people trust

Hey [Name],

[1-2 sentences about how they deploy AI to customers, or a specific integration challenge their users face. Something you found by actually looking at their product.]

Demos work in controlled conditions. Tools people trust survive contact with the actual workflow.

I've crossed that gap a few times. OpenCodeIntel's MCP server: 6 semantic tools, code search, dependency graphs, impact analysis, used inside Cursor and Windsurf on real codebases. Not a prototype. And LCO: users couldn't see token costs in Claude's UI, so I built the interception layer in-browser. SSE stream tap via window.fetch.tee(), real BPE tokenizer, Shadow DOM overlay. Zero backend. The thing that proves I start with user behavior: my portfolio is a full OS in the browser. I analyzed that portfolios bounce in 8 seconds, so I built something that forces you to explore. Average session: 4+ minutes. It's a trap.

What I shipped:
* MCP server with 6 tools in Cursor and Windsurf. Real codebases, real engineers.
* LCO: fixed a real user friction. In-browser SSE interception, zero data leaves the machine.
* Portfolio OS: user behavior first. 8-second bounce became 4-minute session.

15 minutes to talk about deploying AI where it holds up?"""
    },

    # ── 4. CONTEXT ENGINEER ──────────────────────────────────────────────────
    {
        "slug": "context",
        "title": "Context Engineer",
        "color": "#ec4899",
        "tagline": "You proved the model isn't the bottleneck. Context quality is.",
        "sort_order": 3,
        "role_prompt_addition": """ROLE: Context Engineer
PSYCHOLOGICAL FRAME: Make them feel immediately understood, like you've been thinking about the exact problem they're hired to solve. Then show you've gone further than most.

SUBJECT LINE:
"The model isn't the bottleneck. Here's what is."
"Spent a year on context quality. Here's what actually moves it."
Or: something referencing their specific AI product's context or grounding challenge.

THE CORE THESIS (use this):
"Context quality is the bottleneck. Not the model. I spent a year proving it. OpenCodeIntel's retrieval went from ~70% to 87.5% Hit@1, and the single biggest gain came from changing how I chunked code, not which model I used. Naive token splitting destroys function boundaries, class relationships, import chains. AST parsing via Tree-sitter across 8 languages preserves all of it. That one architectural decision outperformed every model swap. The second insight: you can't improve context without measuring it. Built the eval framework (Hit@1, Hit@3, MRR) before touching any optimization."

HOOK (1-2 sentences): Their AI product's specific grounding or context challenge. Something concrete from their docs, blog, or product that shows you've actually looked.

BULLETS, pick 3:
"AST chunking across 8 languages. Single biggest accuracy gain. The architecture beat the model."
"Custom eval framework: Hit@1, Hit@3, MRR per layer. Built measurement first, optimized second."
"Saar: auto-generates CLAUDE.md, .cursorrules from static analysis. Context extraction, automated."
"MCP server with 6 semantic tools. 681 commits. opencodeintel.com is live and real."

CTA: "Got 15 minutes to talk context quality?", peer conversation.

DO NOT: Explain what context engineering is. If this role exists, they know. Skip the definition entirely. Go straight to the insight on line one.""",
        "example_email": """Subject: The model isn't the bottleneck. Here's what is.

Hey [Name],

[1-2 sentences about their AI product's specific context or grounding challenge, something concrete from their docs, product, or a post they've published.]

The model is rarely the problem. Context quality is.

I spent a year proving it with OpenCodeIntel. Three retrieval iterations, measured with a custom eval (Hit@1, Hit@3, MRR). The single biggest accuracy gain came from changing how I chunked code, not from any model change. Naive token splitting destroys semantic boundaries. Tree-sitter AST parsing across 8 languages preserves function relationships, import chains, class hierarchy. That one decision outperformed every embedding model upgrade combined. ~70% to 87.5% Hit@1, and AST parsing moved more of it than everything else.

What I shipped:
* Eval framework first: isolated each layer's contribution before optimizing any of it.
* Saar: auto-generates CLAUDE.md and .cursorrules from deep static analysis. Context extraction, automated.
* Hybrid retrieval: vector + BM25 + reranking. 681 commits. opencodeintel.com is live.

Got 15 minutes to talk context quality?"""
    },

    # ── 5. FULL STACK ENGINEER ───────────────────────────────────────────────
    {
        "slug": "fullstack",
        "title": "Full Stack Engineer",
        "color": "#10b981",
        "tagline": "You build traps. Products people can't stop using.",
        "sort_order": 4,
        "role_prompt_addition": """ROLE: Full Stack Engineer
PSYCHOLOGICAL FRAME: You ship complete products with real users. Not features, not components. You think about users obsessively, even when the user is the recruiter reading your portfolio.

SUBJECT LINE:
"My portfolio is a full OS in the browser. Here's why."
"Complete products. Not tutorial projects."
Or: something specific referencing their product, recent launch, or tech stack.

THE HOOK STORY (use when it maps):
"My portfolio is a full operating system in the browser: window management, file system, app launcher, built from scratch with Next.js 15 and Framer Motion. Not a flex. A deliberate product decision: I analyzed that portfolios bounce in 8 seconds. An OS forces you to click around. Average session: 4+ minutes. It's a trap. It works. That's how I think about every product I build. Start with what the user actually does, engineer backwards."

Use this story when the company values product thinking, design, user experience, or founding-engineer mentality. It proves you think like a product person, not just a coder.

CONNECTION: Tie it to their product. You don't wait for specs. You figure out the user problem, design the experience, ship it.

BULLETS, pick 3 that match this company's scale and domain:
"Portfolio OS: browser OS with window management from scratch. Built for user behavior, not to show off React. 4+ min sessions."
"OpenCodeIntel: React + FastAPI + Supabase + pgvector + GitHub Actions + MCP server. One owner. 681 commits."
"E-commerce API: profiled before adding servers. Found 3 root causes. p95 800ms → 280ms. Checkout conversion +18%."
"LCO: Chrome extension, 3-world TypeScript architecture (MAIN world, content script, service worker). SSE interception, real BPE tokenizer, Shadow DOM. Zero backend."
"Saar: pip installable CLI, auto-generates CLAUDE.md from static analysis. Works with Claude Code, Cursor, Copilot."
"SecureScale: full AWS multi-AZ infra via Terraform. 2 hours to 10 minutes provisioning. One engineer."

CTA: "15 minutes?" The shortest possible. Confident.

DO NOT: List technologies without outcomes. Don't say what you "worked on". Show what you shipped and who used it.""",
        "example_email": """Subject: My portfolio is a full OS in the browser. Here's why.

Hey [Name],

[1-2 sentences about their product, a recent launch, or something specific about how they build. Show you've actually looked.]

My portfolio is a full operating system in the browser: window management, file system, app launcher, built from scratch with Next.js 15 and Framer Motion. Not a flex. I analyzed that portfolios bounce in 8 seconds, so I built something that forces you to explore. Average session: 4+ minutes. It's a trap. This is how I think about every product: start with what the user actually does, engineer backwards.

OpenCodeIntel is the same thinking at scale: React frontend, FastAPI backend, Supabase, pgvector, GitHub Actions CI/CD, MCP server. Full stack. One owner. 681 commits. Then LCO: a Chrome extension with a 3-world isolation architecture because the problem required it. No shortcuts.

What I shipped:
* Portfolio OS: 8-second bounce became 4-minute session. User behavior first.
* OpenCodeIntel: semantic code search, 87.5% Hit@1, MCP tools in Cursor and Windsurf.
* LCO: SSE interception, real BPE tokenizer, Shadow DOM overlay. Zero backend. TypeScript.

15 minutes?"""
    },

    # ── 6. CLOUD / DEVOPS / SRE ──────────────────────────────────────────────
    {
        "slug": "cloud",
        "title": "Cloud / DevOps / SRE",
        "color": "#06b6d4",
        "tagline": "Taught Terraform to 180 students. Then built the infra I taught.",
        "sort_order": 5,
        "role_prompt_addition": """ROLE: Cloud / DevOps / SRE / Platform Engineer
PSYCHOLOGICAL FRAME: Teaching infrastructure forces depth you can't fake . Then you go prove it.

SUBJECT LINE:
"Wrote the AWS curriculum for 180+ students. Then I built this."
"Taught Terraform to grad students. Here's the infra I shipped after."
Or: something specific about their infrastructure challenges, scaling story, or a post about their platform.

HOOK (1-2 sentences): Their specific infra setup, a scaling challenge they've shared publicly, or something about their engineering culture around reliability. Be concrete.

CONNECTION:
"I'm a Graduate TA for Cloud Computing at Northeastern. I didn't just take the course, I wrote the lab curriculum for Docker, GitHub Actions, and Terraform used across 3 sections, 180+ students. Teaching infrastructure forces you to understand it at a level you genuinely cannot fake. Then I went and built SecureScale: multi-AZ AWS via modular Terraform, defense-in-depth with 4 KMS keys, IAM least-privilege, NAT isolation, zero-downtime CI/CD with 30-second boot via immutable Packer AMI builds."

BULLETS, pick 3:
"Wrote the Docker, GitHub Actions, Terraform curriculum. 180+ students, 3 sections. Adopted as official course content. Means it actually works."
"SecureScale: provisioning from 2 hours to 10 minutes. Cloud spend down 30%. Zero-downtime with 30-second Packer AMI boot."
"Defense-in-depth: 4 KMS keys, IAM least-privilege, NAT isolation. Security architecture, not just deployment."
"Production e-commerce: profiled before recommending infra changes. Found 3 root causes. p95 800ms → 280ms. Checkout +18%. Right answer starts with measurement, not provisioning."
"CloudWatch + SNS alerting. You can't fix what you can't see."

CTA: "15 minutes to talk infrastructure?" Direct.

DO NOT: List AWS services like a resume. Every bullet shows a decision, a constraint, and an outcome.""",
        "example_email": """Subject: Wrote the AWS curriculum for 180+ students. Then I built this.

Hey [Name],

[1-2 sentences about their infrastructure challenges, scaling story, or something specific about how they run their platform.]

I'm a Graduate TA for Cloud Computing at Northeastern. I wrote the lab curriculum for Docker, GitHub Actions, and Terraform, used across 3 sections, 180+ students. Teaching infrastructure forces you to understand it at a level you can't fake. Then I went and proved it.

SecureScale: multi-AZ AWS via modular Terraform. Defense-in-depth with 4 KMS encryption keys, IAM least-privilege, NAT isolation. Zero-downtime CI/CD with 30-second boot via immutable Packer AMI builds.

What I shipped:
* Provisioning: 2 hours to 10 minutes. Cloud spend down 30%.
* Zero-downtime deploys. 30-second boot. CloudWatch + SNS observability.
* Curriculum adopted as official course content. That means it actually works.

15 minutes to talk infrastructure?"""
    },

    # ── 7. RAG ENGINEER ──────────────────────────────────────────────────────
    {
        "slug": "rag",
        "title": "RAG Engineer",
        "color": "#d946ef",
        "tagline": "Three iterations. Custom eval. The chunking beat the model.",
        "sort_order": 6,
        "role_prompt_addition": """ROLE: RAG / Retrieval Engineer
PSYCHOLOGICAL FRAME: One retrieval engineer to another. Skip the setup, go straight to architecture decisions. This is a technical peer conversation, not a job pitch.

SUBJECT LINE:
"Three iterations on a retrieval pipeline. Here's what moved accuracy."
"Your embedding model isn't the bottleneck. This was."
Or: something directly referencing their retrieval or search architecture, specific models they use, or a technical post about their RAG setup.

THE STORY (lead with this):
"Three iterations, measured with a custom eval (Hit@1, Hit@3, MRR). Pure vector: ~70%. Added BM25: ~80%. Cohere reranking: 87.5%. But here's what actually moved accuracy the most: switching from naive token chunking to Tree-sitter AST parsing across 8 languages. Naive token splitting destroys function boundaries, class relationships, import chains. AST parsing preserves them. That one architectural decision outperformed every model swap combined. The model was never the bottleneck."

HOOK (1-2 sentences): Their specific retrieval architecture: a blog post, a paper they've referenced, a model they use publicly, or a product challenge their system faces. Technical and specific.

BULLETS, pick 3:
"Custom eval framework: Hit@1, Hit@3, MRR at each layer. Built the measurement before touching any optimization."
"Hybrid retrieval: voyage-code-3 + BM25 + Cohere reranking. 87.5% Hit@1 on code search."
"AST chunking via Tree-sitter across 8 languages. Bigger accuracy gain than any model swap."
"Saar: codebase DNA extraction, auto-generates context files. Context quality is the real retrieval problem."

CTA: "15 minutes to compare retrieval architectures?" Peer conversation.

DO NOT: Explain what RAG means. Don't explain embeddings. Don't explain vector search. They know all of this. Go straight to the specific architectural insight.""",
        "example_email": """Subject: Three iterations on a retrieval pipeline. Here's what moved accuracy.

Hey [Name],

[1-2 sentences about their retrieval architecture, a model they use, or a specific technical challenge in their product. Technical and specific, show you've actually looked.]

Most accuracy gains in retrieval don't come from the model. They come from how you chunk.

Three iterations on OpenCodeIntel's pipeline, measured with a custom eval: Hit@1, Hit@3, MRR at each step. Pure vector: ~70%. Added BM25: ~80%. Cohere reranking: 87.5%. The single biggest jump? Switching from naive token chunking to Tree-sitter AST parsing across 8 languages. AST parsing preserves function boundaries, class hierarchy, import chains. Naive token splitting destroys them. That one change outperformed every model upgrade combined.

What I shipped:
* Custom eval framework. Isolated each layer's contribution before optimizing anything.
* Hybrid retrieval: voyage-code-3 + BM25 + reranking. 87.5% Hit@1 on code.
* Saar: extracts codebase DNA, auto-generates context files. Context quality is the actual bottleneck.

15 minutes to compare retrieval architectures?"""
    },

    # ── 8. BACKEND ENGINEER ──────────────────────────────────────────────────
    {
        "slug": "backend",
        "title": "Backend Engineer",
        "color": "#64748b",
        "tagline": "Eval framework first. Measured every iteration. 87.5% Hit@1.",
        "sort_order": 7,
        "role_prompt_addition": """ROLE: Backend Engineer
PSYCHOLOGICAL FRAME: Systematic thinker who measures before optimizing. The discipline shows in the architecture. Lead with the eval-first mindset and real systems thinking.

SUBJECT LINE:
"Three retrieval iterations. Measured each one. Here's what moved."
"Eval framework first. Then optimize. Here's what I found."
"Three root causes before recommending infra. p95 800ms → 280ms."
Or: something referencing their specific backend challenges, their scale, or a technical decision they've made publicly.

HOOK (1-2 sentences): Their specific backend challenges: scale, latency, a particular architecture decision they've talked about publicly. Something that shows you know what problem they're dealing with.

THE STORY (use this):
"I built the eval framework for OpenCodeIntel before touching any optimization. Hit@1, Hit@3, MRR at each retrieval layer. Then three measured iterations: pure vector (~70%), add BM25 (~80%), Cohere reranking (87.5% Hit@1). The single biggest accuracy jump came from switching how I chunked code. Naive token splitting destroys function boundaries, import chains, class relationships. Tree-sitter AST parsing across 8 languages preserves them. One architectural decision outperformed every model swap. Then LCO: needed to intercept Claude's SSE stream without disrupting the UI. Solution: window.fetch.tee(), three-world isolation (MAIN world, content script, service worker), real BPE tokenization via js-tiktoken. Zero backend. The constraint forced a cleaner architecture than a server would have."

BULLETS, pick 3:
"Eval framework before touching anything. Hit@1, Hit@3, MRR per layer. Can't optimize what you haven't measured."
"AST chunking across 8 languages. Biggest accuracy gain. Beat every model swap. Architectural decision, not a model choice."
"E-commerce API: profiled before adding servers. Found 3 root causes. p95 800ms → 280ms. Checkout conversion +18%."
"LCO: 3-world TypeScript architecture, SSE stream interception, real BPE tokenizer. Zero backend. Constraint made it cleaner."
"SecureScale: provisioning from 2 hours to 10 minutes. Cloud spend down 30%. Multi-AZ Terraform, zero-downtime CI/CD."
"OpenCodeIntel: FastAPI + pgvector, hybrid retrieval at 87.5% Hit@1. 681 commits. Live."

CTA: "15 minutes to talk backend?", direct, casual.

DO NOT: Say "passionate." Use em dashes. List tech without outcomes. Go over 130 words. Start with your name or school.""",
        "example_email": """Subject: Three retrieval iterations. Measured each one. Here's what moved.

Hey [Name],

[1-2 sentences about their specific backend challenges or scale, something concrete. Show you know what problem they're dealing with.]

I like backend problems where the numbers are honest.

I built the eval framework for OpenCodeIntel before touching any optimization. Hit@1, Hit@3, MRR at each retrieval layer. Three measured iterations: pure vector (~70%), add BM25 (~80%), Cohere reranking (87.5% Hit@1). The biggest jump wasn't the model. It was switching from naive token chunking to Tree-sitter AST parsing across 8 languages. One architectural decision outperformed every model swap combined.

LCO is the same discipline. Intercepted Claude's SSE stream with window.fetch.tee(), three-world TypeScript isolation, real BPE tokenizer. No backend. The constraint forced a cleaner architecture than a server would have.

What I shipped:
* Eval framework first. Measured before optimizing. Every layer isolated.
* AST chunking. Biggest accuracy gain. Not the model.
* SecureScale: 2 hours to 10 minutes provisioning. Cloud spend down 30%.

15 minutes to talk backend?"""
    },
]


def run():
    db = get_db()
    uid = DEVANSHU_USER_ID

    # 1. Update profile
    print("Updating profile...")
    db.table("profiles").update({
        "full_name": "Devanshu Chicholikar",
        "background": BACKGROUND,
        "sign_off_block": SIGN_OFF,
        "links_block": LINKS_BLOCK,
        "projects": PROJECTS,
    }).eq("user_id", uid).execute()
    print("  Profile updated.")

    # 2. Nuke and re-seed templates
    print("Rebuilding templates...")
    # Null out role_template_id on any applications before deleting templates (FK constraint)
    db.table("applications").update({"role_template_id": None}).eq("user_id", uid).execute()
    db.table("role_templates").delete().eq("user_id", uid).execute()
    for t in TEMPLATES:
        db.table("role_templates").insert({
            "id": str(uuid.uuid4()),
            "user_id": uid,
            "system_prompt": "",
            **t,
        }).execute()
        print(f"  {t['slug']}: {t['tagline']}")

    print("\nDone. Profile and all 8 templates rebuilt.")


if __name__ == "__main__":
    run()
