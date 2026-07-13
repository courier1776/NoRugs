from dataclasses import dataclass
from typing import Any


@dataclass
class RiskResult:
    overall_score: float
    risk_level: str
    confidence_score: float
    summary: str
    factors: list[dict[str, Any]]


def clamp(value: float, minimum: float = 0, maximum: float = 100) -> float:
    return max(minimum, min(value, maximum))


def market_cap_risk(market_cap: float | None) -> float:
    if market_cap is None:
        return 70

    if market_cap >= 10_000_000_000:
        return 10
    if market_cap >= 1_000_000_000:
        return 20
    if market_cap >= 100_000_000:
        return 40
    if market_cap >= 10_000_000:
        return 65

    return 90


def volume_risk(
    market_cap: float | None,
    volume_24h: float | None,
) -> float:
    if not market_cap or volume_24h is None:
        return 70

    ratio = volume_24h / market_cap

    if ratio >= 0.10:
        return 15
    if ratio >= 0.05:
        return 30
    if ratio >= 0.01:
        return 50
    if ratio >= 0.005:
        return 70

    return 90


def volatility_risk(change_24h: float | None) -> float:
    if change_24h is None:
        return 60

    absolute_change = abs(change_24h)

    if absolute_change <= 5:
        return 15
    if absolute_change <= 10:
        return 30
    if absolute_change <= 20:
        return 55
    if absolute_change <= 40:
        return 75

    return 95


def supply_risk(
    circulating_supply: float | None,
    total_supply: float | None,
) -> float:
    if not circulating_supply or not total_supply:
        return 60

    ratio = circulating_supply / total_supply

    if ratio >= 0.85:
        return 15
    if ratio >= 0.60:
        return 35
    if ratio >= 0.35:
        return 60

    return 85


def calculate_risk(coin: dict[str, Any]) -> RiskResult:
    market_data = coin.get("market_data", {})

    market_cap = market_data.get("market_cap", {}).get("usd")
    volume_24h = market_data.get("total_volume", {}).get("usd")
    change_24h = market_data.get("price_change_percentage_24h")
    circulating_supply = market_data.get("circulating_supply")
    total_supply = market_data.get("total_supply")

    factors = [
        {
            "name": "Market Capitalization",
            "score": market_cap_risk(market_cap),
            "weight": 0.30,
            "explanation": (
                "Lower-market-cap assets can be easier to manipulate."
            ),
            "evidence": {"market_cap_usd": market_cap},
        },
        {
            "name": "Trading Activity",
            "score": volume_risk(market_cap, volume_24h),
            "weight": 0.30,
            "explanation": (
                "Low trading volume relative to market capitalization "
                "can indicate weak liquidity or limited activity."
            ),
            "evidence": {
                "market_cap_usd": market_cap,
                "volume_24h_usd": volume_24h,
            },
        },
        {
            "name": "Price Volatility",
            "score": volatility_risk(change_24h),
            "weight": 0.25,
            "explanation": (
                "Extreme 24-hour price movement increases short-term risk."
            ),
            "evidence": {"price_change_24h_pct": change_24h},
        },
        {
            "name": "Supply Distribution",
            "score": supply_risk(circulating_supply, total_supply),
            "weight": 0.15,
            "explanation": (
                "A low circulating-to-total supply ratio may create "
                "future dilution risk."
            ),
            "evidence": {
                "circulating_supply": circulating_supply,
                "total_supply": total_supply,
            },
        },
    ]

    weighted_score = sum(
        factor["score"] * factor["weight"]
        for factor in factors
    )

    overall_score = round(clamp(weighted_score), 2)

    available_values = [
        market_cap,
        volume_24h,
        change_24h,
        circulating_supply,
        total_supply,
    ]

    completed = sum(value is not None for value in available_values)
    confidence_score = round((completed / len(available_values)) * 70, 2)

    if overall_score < 25:
        risk_level = "LOW"
    elif overall_score < 50:
        risk_level = "MODERATE"
    elif overall_score < 75:
        risk_level = "HIGH"
    else:
        risk_level = "CRITICAL"

    summary = (
        f"{coin['name']} received a preliminary risk score of "
        f"{overall_score}/100 based on market capitalization, trading "
        "activity, volatility, and supply information. Wallet, liquidity, "
        "and smart-contract analysis have not yet been included."
    )

    return RiskResult(
        overall_score=overall_score,
        risk_level=risk_level,
        confidence_score=confidence_score,
        summary=summary,
        factors=factors,
    )
    
def normalize_market_coin(
    coin: dict[str, Any],
) -> dict[str, Any]:
    return {
        "id": coin["id"],
        "name": coin["name"],
        "symbol": coin["symbol"],
        "market_data": {
            "market_cap": {
                "usd": coin.get("market_cap")
            },
            "total_volume": {
                "usd": coin.get("total_volume")
            },
            "price_change_percentage_24h": coin.get(
                "price_change_percentage_24h_in_currency",
                coin.get("price_change_percentage_24h"),
            ),
            "circulating_supply": coin.get(
                "circulating_supply"
            ),
            "total_supply": coin.get("total_supply"),
        },
    }


def calculate_market_risk(
    coin: dict[str, Any],
) -> RiskResult:
    normalized_coin = normalize_market_coin(coin)
    return calculate_risk(normalized_coin)