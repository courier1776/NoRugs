from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict


class CoinSummary(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    cryptocurrency_id: int
    external_market_id: str | None
    name: str
    symbol: str
    logo_url: str | None

    price_usd: Decimal | None
    market_cap_usd: Decimal | None
    volume_24h_usd: Decimal | None
    price_change_24h_pct: Decimal | None
    market_rank: int | None

    overall_risk_score: Decimal | None
    risk_level: str
    confidence_score: Decimal | None
    risk_summary: str | None

    market_data_updated_at: datetime | None
    risk_assessed_at: datetime | None


class RiskFactor(BaseModel):
    factor_name: str
    factor_score: Decimal
    weight: Decimal
    weighted_score: Decimal | None
    explanation: str | None
    evidence: dict


class CoinDetail(CoinSummary):
    description: str | None
    website_url: str | None
    circulating_supply: Decimal | None
    total_supply: Decimal | None
    max_supply: Decimal | None
    risk_factors: list[RiskFactor]


class DashboardStats(BaseModel):
    total_coins: int
    low_risk: int
    moderate_risk: int
    high_risk: int
    critical_risk: int
    average_risk_score: Decimal | None


class HealthResponse(BaseModel):
    status: str
    database: str