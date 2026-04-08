from datetime import datetime

from pydantic import BaseModel


class ProjectCreate(BaseModel):
    name: str
    company_name: str | None = None
    company_description: str | None = None
    industry: str | None = None
    target_market: str | None = None


class ProjectUpdate(BaseModel):
    name: str | None = None
    company_name: str | None = None
    company_description: str | None = None
    industry: str | None = None
    target_market: str | None = None
    status: str | None = None


class ProjectResponse(BaseModel):
    id: str
    name: str
    company_name: str | None = None
    company_description: str | None = None
    industry: str | None = None
    products: list = []
    target_market: str | None = None
    competitors: list = []
    research_data: dict = {}
    strategy_notes: dict = {}
    status: str
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}
