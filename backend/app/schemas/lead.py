from typing import Optional

from pydantic import BaseModel, Field


class LeadInput(BaseModel):
    postcode: str = Field(..., min_length=3, max_length=12)
    product_interest: str = Field(..., min_length=2, max_length=100)
    household_size: Optional[int] = Field(default=None, ge=1, le=20)
    annual_consumption_kwh: Optional[int] = Field(default=None, ge=0, le=100000)
    budget_band: Optional[str] = Field(default=None, max_length=50)
    customer_goal: Optional[str] = Field(default=None, max_length=200)
