from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.config import settings
from app.auth.router import router as auth_router
from app.routers.profiles import router as profiles_router
from app.routers.templates import router as templates_router
from app.routers.companies import router as companies_router
from app.routers.applications import router as applications_router
from app.routers.emails import router as emails_router
from app.routers.contacts import router as contacts_router
from app.routers.outreach import router as outreach_router
from app.routers.stats import router as stats_router
from app.routers.fit_analyzer import router as fit_router

app = FastAPI(title="Cold Outreach API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins.split(","),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_router)
app.include_router(profiles_router)
app.include_router(templates_router)
app.include_router(companies_router)
app.include_router(applications_router)
app.include_router(emails_router)
app.include_router(contacts_router)
app.include_router(outreach_router)
app.include_router(stats_router)
app.include_router(fit_router)


@app.get("/api/health")
def health():
    return {"status": "ok"}
