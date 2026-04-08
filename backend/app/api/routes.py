from fastapi import APIRouter

from app.schemas.lead import LeadInput
from app.services.ai_service import generate_ai_summary
from app.services.enrichment import enrich_lead
from app.services.finance import build_financing_options
from app.services.recommender import recommend_packages
from app.services.report_builder import build_report

router = APIRouter()


@router.get("/health")
def health():
    return {"status": "ok"}


@router.post("/report/generate")
def generate_report(payload: LeadInput):
    enriched = enrich_lead(payload.model_dump())
    packages, best_package = recommend_packages(enriched)
    financing = build_financing_options(packages, best_package)
    ai_summary = generate_ai_summary(enriched, packages, financing, best_package)
    report = build_report(enriched, packages, financing, ai_summary, best_package)

    return {
        "success": True,
        "report": report,
    }
