from enum import Enum

from pydantic import BaseModel


class SalesPhase(str, Enum):
    DATA_GATHERING = "data_gathering"
    RESEARCH = "research"
    STRATEGY = "strategy"
    DELIVERABLE = "deliverable"
    COMPLETE = "complete"


class ProductInfo(BaseModel):
    name: str
    description: str = ""
    price: str = ""
    key_features: list[str] = []


class CompetitorInfo(BaseModel):
    name: str
    description: str = ""
    strengths: list[str] = []
    weaknesses: list[str] = []
    market_share: str = ""


class ObjectionResponse(BaseModel):
    objection: str
    response: str


class SalesData(BaseModel):
    """Structured data accumulated by agents throughout the sales pipeline."""

    # Phase tracking
    phase: SalesPhase = SalesPhase.DATA_GATHERING

    # Data gathering fields
    company_name: str | None = None
    company_description: str | None = None
    industry: str | None = None
    products: list[ProductInfo] = []
    target_market: str | None = None
    pain_points: list[str] = []
    unique_selling_points: list[str] = []

    # Research fields
    competitors: list[CompetitorInfo] = []
    market_trends: list[str] = []
    market_size: str | None = None
    industry_insights: list[str] = []

    # Strategy fields
    positioning: str | None = None
    value_proposition: str | None = None
    key_messages: list[str] = []
    objections: list[ObjectionResponse] = []
    target_personas: list[str] = []

    def is_gathering_complete(self) -> bool:
        """Check if minimum data has been gathered to proceed."""
        return bool(
            self.company_name
            and self.company_description
            and self.products
            and self.target_market
        )

    def is_research_complete(self) -> bool:
        return bool(self.competitors or self.market_trends)

    def is_strategy_complete(self) -> bool:
        return bool(self.positioning and self.key_messages)
