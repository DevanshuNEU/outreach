"""
Seed Devanshu's 8 role templates into the database.
Run: python -m app.seed_templates <user_id>
"""
import sys
import uuid
from app.database import get_db

TEMPLATES = [
    {
        "slug": "swe",
        "title": "Software Engineer",
        "color": "#3b82f6",
        "tagline": "You have production receipts. Not school project screenshots.",
        "role_prompt_addition": """ROLE: Software Engineer
LEAD WITH: Real production systems, real users, real metrics. The e-commerce platform or OpenCodeIntel depending on what the company builds.
SHOW: Engineering maturity. You measure things. You optimize bottlenecks. You ship CI/CD pipelines that actually work.
DON'T: Mention "Jaksh Enterprise" by name. Nobody knows it. Lead with what you built.""",
        "example_email": """Subject: p95 from 800ms to 280ms. Three changes, not thirty.

Hey [Name],

[Specific thing about their product/blog/tech decision goes here. 1-2 sentences max.]

I built a platform handling 15K+ daily API requests where checkout was dying during peak traffic. The fix wasn't complicated. Async event queues to decouple writes. B-tree indexes on hot query paths. Redis for session data. p95 dropped from 800ms to 280ms. Checkout completion went up 18%.

Now I'm 650+ commits deep into OpenCodeIntel, an open-source AI code intelligence platform.

What I shipped:
* Retrieval accuracy started at ~70%. Three architecture iterations later: 87.5% Hit@1. Built the eval framework to prove it.
* MCP server with 6 tools. Engineers use it in Cursor and Windsurf on real codebases right now.
* Zero-downtime CI/CD. Releases went from 2 weeks to 3 days.

15 minutes to talk shop?""",
        "sort_order": 0,
    },
    {
        "slug": "ai-ml",
        "title": "AI/ML Engineer",
        "color": "#8b5cf6",
        "tagline": "Most people read about RAG. You built one and measured it.",
        "role_prompt_addition": """ROLE: AI/ML Engineer
LEAD WITH: OpenCodeIntel's RAG pipeline. The key differentiator is you have EVALUATION METRICS. Most people just say "it works."
SHOW: You iterate. You measure. You make architecture decisions based on data, not vibes. Three iterations to go from 70% to 87.5%.
DON'T: Over-explain what RAG is. They know. Hit them with results and decisions.""",
        "example_email": """Subject: Most RAG pipelines skip evaluation. Mine didn't.

Hey [Name],

[Specific thing about their AI product/retrieval challenge/model deployment goes here.]

Pure vector search got me to ~70% retrieval accuracy on code. That's what most people ship and call it done. I didn't.

I spent a year building OpenCodeIntel, an open-source code intelligence platform. The retrieval pipeline went through three iterations. Vector embeddings alone weren't enough. Adding BM25 for keyword precision helped. Cohere reranking on top pushed it to 87.5% Hit@1. But the real breakthrough was building an eval framework to actually measure what was working at each step.

What I shipped:
* Hybrid RAG pipeline: voyage-code-3 + BM25 + reranking. Custom eval measuring Hit@1, Hit@3, and MRR.
* Tree-sitter AST chunking across 8 languages. Naive token splitting was destroying semantic meaning.
* Saar: auto-generates CLAUDE.md from deep static analysis. Because AI agents need context, not just code.
* 650+ commits across the org. This is not a weekend project.

15 minutes to compare notes on retrieval quality?""",
        "sort_order": 1,
    },
    {
        "slug": "fde",
        "title": "Forward-Deployed Engineer",
        "color": "#f59e0b",
        "tagline": "You've been doing this job before the title existed.",
        "role_prompt_addition": """ROLE: Forward-Deployed Engineer
LEAD WITH: You build tools for specific users and specific problems. MCP server = tools AI agents actually use. TestPulse = built for Stably AI. ModerationKit = built for SafetyKit. You start with the user problem, not the technology.
SHOW: The difference between a demo and a tool people trust. You've crossed that gap multiple times.
DON'T: Use the phrase "bridge the gap" (overused). Show, don't tell.""",
        "example_email": """Subject: Built three AI tools for three different companies. All shipped.

Hey [Name],

[Specific thing about how they deploy AI to customers / their integration challenges goes here.]

There's a massive difference between an AI demo and a tool people actually rely on. I've shipped the latter three times now.

OpenCodeIntel: MCP server with 6 semantic tools. Engineers use it in Cursor and Windsurf on real codebases. Not a proof of concept.

TestPulse AI: test intelligence dashboard built for Stably AI's specific Playwright workflow. ModerationKit: content moderation built for SafetyKit's platform needs. Both started with a user problem, not a technology looking for one.

What I shipped:
* MCP server that AI agents call in production. Semantic search, dependency graphs, impact analysis.
* Saar: auto-generates CLAUDE.md from static analysis. Turns any codebase into context an AI can use.
* 650+ commits across the OpenCodeIntel org. One-click GitHub OAuth import. Full React + FastAPI stack.

15 minutes to talk about deploying AI where it actually creates value?""",
        "sort_order": 2,
    },
    {
        "slug": "context",
        "title": "Context Engineer",
        "color": "#ec4899",
        "tagline": "Your whole GitHub bio is 'Building the context layer for AI.' This IS the job.",
        "role_prompt_addition": """ROLE: Context Engineer
LEAD WITH: You've spent a year solving the exact problem this role exists for: giving AI the right information at the right time.
SHOW: Why context quality is the bottleneck. Your chunking decisions. Why AST > naive splitting. The measurable impact of each retrieval improvement.
DON'T: Explain what context engineering is. If they have this role, they know. Show your architecture decisions.""",
        "example_email": """Subject: Spent a year on why AI can't understand codebases. Fixed it.

Hey [Name],

[Specific thing about their AI product's context/grounding challenges goes here.]

The hardest part of making AI useful for developers isn't the model. It's context. Give it wrong context and it hallucinates confidently. Give it right context and it's genuinely useful.

I've spent a year building OpenCodeIntel to solve this. The key insight: how you chunk code matters more than which embedding model you pick. Naive token splitting destroys function boundaries, class relationships, import chains. Tree-sitter AST parsing preserves all of it.

What I shipped:
* Semantic chunking via AST parsing across 8 languages. This single change moved accuracy more than any model swap.
* Hybrid retrieval: vector + BM25 + reranking. 87.5% Hit@1. Built the eval framework to isolate what each layer contributes.
* Saar: auto-generates CLAUDE.md and .cursorrules from deep static analysis. Context extraction, automated.
* 650+ commits. This isn't a side project. It's the thing I work on.

Got 15 minutes to talk context quality?""",
        "sort_order": 3,
    },
    {
        "slug": "fullstack",
        "title": "Full Stack Engineer",
        "color": "#10b981",
        "tagline": "You build entire products. Multiple times. From scratch.",
        "role_prompt_addition": """ROLE: Full Stack Engineer
LEAD WITH: You ship complete products. Not features. Not components. Products with users.
SHOW: Range and depth. React frontend + FastAPI backend + Supabase + CI/CD. Multiple projects, each with 100+ commits.
DON'T: Just list technologies. Show what you built with them and why it mattered.""",
        "example_email": """Subject: My portfolio is a working operating system. In the browser.

Hey [Name],

[Specific thing about their product / what they're building goes here.]

I got bored of template portfolios so I built mine as a full operating system. Window management, file system, app launcher, all from scratch with Next.js 15 and Framer Motion. That's at devanshuchicholikar.me.

But the real work is OpenCodeIntel. AI code intelligence platform where I own the whole stack: React frontend, FastAPI backend, Supabase data layer, GitHub Actions CI/CD, MCP server integration. 650+ commits.

What I shipped:
* OpenCodeIntel: semantic code search with 87.5% accuracy. Full product, not a tutorial project.
* Financial Copilot: AI expense tracking with receipt processing and NL analytics. 196 commits.
* Production e-commerce platform serving 12K+ monthly users with 15K+ daily API requests.

Each one is a complete product. Frontend to database to deploy pipeline.

Got 15 minutes?""",
        "sort_order": 4,
    },
    {
        "slug": "cloud",
        "title": "Cloud / DevOps / SRE",
        "color": "#06b6d4",
        "tagline": "You teach AWS to 180+ students. Then you go build with it.",
        "role_prompt_addition": """ROLE: Cloud / DevOps / SRE
LEAD WITH: You don't just use infrastructure tools. You wrote the curriculum for teaching them to 180+ students. Then you built production-grade infra that actually runs.
SHOW: SecureScale's architecture decisions. Why specific security choices. The metrics (2hrs to 10min provisioning, 30% cost reduction).
DON'T: List AWS services. Show what you built and what it achieved.""",
        "example_email": """Subject: Wrote the AWS infrastructure curriculum for 180+ grad students. Then I built this.

Hey [Name],

[Specific thing about their infrastructure / scaling challenges / DevOps culture goes here.]

I'm a Graduate TA for Cloud Computing at Northeastern. I wrote the lab curriculum for Docker, GitHub Actions, and Terraform automation. It's used across 3 sections serving 180+ students now.

Teaching infrastructure forces you to understand it deeply. So I built SecureScale: production-grade multi-AZ AWS setup via modular Terraform. Not a tutorial deployment. Defense-in-depth security with 4 KMS encryption keys, IAM least-privilege, NAT isolation.

What I shipped:
* Provisioning went from 2 hours to 10 minutes. Cloud spend down 30% via right-sizing and S3 lifecycle policies.
* Zero-downtime deployments with 30-second boot via immutable Packer AMI builds.
* CloudWatch observability + SNS alerting pipeline. You can't fix what you can't see.
* Curriculum adopted as official course content. That means it actually works.

15 minutes to talk infrastructure?""",
        "sort_order": 5,
    },
    {
        "slug": "rag",
        "title": "RAG Engineer",
        "color": "#d946ef",
        "tagline": "This role pays $110K-$180K. You literally built the thing.",
        "role_prompt_addition": """ROLE: RAG Engineer
LEAD WITH: Your retrieval architecture. The three iterations. The eval framework. The specific accuracy numbers.
SHOW: Architecture decisions with reasoning. Why hybrid > pure vector. Why AST chunking > naive splitting. Why evaluation matters more than model choice.
DON'T: Explain what RAG is. These people know. Hit them with your architecture story.""",
        "example_email": """Subject: Three iterations on a RAG pipeline. Here's what actually moved accuracy.

Hey [Name],

[Specific thing about their retrieval/search/AI grounding challenges goes here.]

I've been building retrieval systems for a year. Here's what I learned: most of the accuracy gains come from chunking and reranking, not from swapping embedding models.

OpenCodeIntel is my open-source code intelligence platform. The retrieval pipeline went through three major iterations. Pure vector search: ~70%. Adding BM25 keyword matching: ~80%. Cohere reranking on top: 87.5% Hit@1. But the real differentiator was switching from naive token chunking to Tree-sitter AST parsing. That single change moved accuracy more than any model upgrade.

What I shipped:
* Custom eval framework measuring Hit@1, Hit@3, MRR. Can't improve what you can't measure.
* pgvector indexing processing 10K+ code symbols per repo. voyage-code-3 embeddings.
* Saar: extracts codebase DNA. Auto-generates CLAUDE.md and .cursorrules from static analysis.
* 650+ commits. Three repos in the OpenCodeIntel org. This is what I do.

15 minutes to compare retrieval architectures?""",
        "sort_order": 6,
    },
    {
        "slug": "backend",
        "title": "Backend Engineer",
        "color": "#64748b",
        "tagline": "800ms to 280ms is not a resume bullet. It's a receipt.",
        "role_prompt_addition": """ROLE: Backend Engineer
LEAD WITH: The latency story. Three specific changes, measurable outcome. Then OpenCodeIntel's backend.
SHOW: You think about performance systematically. You measure before and after. You make specific architectural choices for specific reasons.
DON'T: Lead with Jaksh by name. Lead with what you built and measured.""",
        "example_email": """Subject: Three changes. p95 dropped from 800ms to 280ms. Checkout completion up 18%.

Hey [Name],

[Specific thing about their backend challenges / scale / architecture goes here.]

I like backend problems where you can see the numbers move. My favorite: a platform doing 15K+ daily API requests where checkout was choking during peak traffic.

Three changes, not thirty. Async event queues to decouple write-heavy operations. B-tree indexes on the query paths that were actually hot (not all of them). Redis for session and catalog caching. p95 went from 800ms to 280ms. Checkout completion up 18%.

Now I'm building the backend for OpenCodeIntel: FastAPI serving hybrid retrieval queries against pgvector, processing 10K+ code symbols per repository.

What I shipped:
* Event-driven async architecture. Measured throughput before and after each change.
* Hybrid search backend: vector + BM25 + reranking. 87.5% Hit@1 accuracy.
* CI/CD pipeline compressing releases from 2 weeks to 3 days. Zero-downtime deploys.
* 650+ commits across the OpenCodeIntel org.

15 minutes to talk backend performance?""",
        "sort_order": 7,
    },
]


def seed(user_id: str):
    db = get_db()
    for t in TEMPLATES:
        existing = (
            db.table("role_templates")
            .select("id")
            .eq("user_id", user_id)
            .eq("slug", t["slug"])
            .execute()
        )
        if existing.data:
            print(f"  Skipping {t['slug']} (already exists)")
            continue

        db.table("role_templates").insert({
            "id": str(uuid.uuid4()),
            "user_id": user_id,
            **t,
            "system_prompt": "",
        }).execute()
        print(f"  Created {t['slug']}")

    print("Done.")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python -m app.seed_templates <user_id>")
        sys.exit(1)
    seed(sys.argv[1])
