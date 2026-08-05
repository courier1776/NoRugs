from __future__ import annotations

from decimal import Decimal, InvalidOperation

from norugs_scraper.database import Database


class RiskScorer:
    """Market-data screening model using consistently available live fields.

    Higher scores indicate higher preliminary market risk. The model does not
    silently turn missing optional evidence into zero and does not claim that
    any cryptocurrency is a safe investment.
    """

    def __init__(self, db: Database) -> None:
        self.db = db

    @staticmethod
    def number(value: object) -> Decimal | None:
        if value is None:
            return None
        try:
            return Decimal(str(value))
        except (InvalidOperation, TypeError, ValueError):
            return None

    @staticmethod
    def clamp(value: Decimal) -> Decimal:
        return max(Decimal("0"), min(Decimal("100"), value))

    @staticmethod
    def capitalization_score(value: Decimal | None) -> Decimal:
        if value is None:
            return Decimal("50")
        if value >= Decimal("100000000000"):
            return Decimal("8")
        if value >= Decimal("10000000000"):
            return Decimal("15")
        if value >= Decimal("1000000000"):
            return Decimal("28")
        if value >= Decimal("100000000"):
            return Decimal("45")
        if value >= Decimal("10000000"):
            return Decimal("65")
        return Decimal("82")

    @staticmethod
    def rank_score(value: int | None) -> Decimal:
        if value is None:
            return Decimal("50")
        if value <= 10:
            return Decimal("8")
        if value <= 25:
            return Decimal("15")
        if value <= 100:
            return Decimal("30")
        if value <= 250:
            return Decimal("48")
        if value <= 500:
            return Decimal("62")
        return Decimal("78")

    @staticmethod
    def activity_score(volume: Decimal | None, cap: Decimal | None) -> Decimal:
        if volume is None or cap is None or cap <= 0:
            return Decimal("50")
        ratio = volume / cap
        if ratio >= Decimal("0.15"):
            return Decimal("10")
        if ratio >= Decimal("0.08"):
            return Decimal("18")
        if ratio >= Decimal("0.03"):
            return Decimal("28")
        if ratio >= Decimal("0.01"):
            return Decimal("42")
        if ratio >= Decimal("0.003"):
            return Decimal("60")
        return Decimal("75")

    @staticmethod
    def volatility_score(change: Decimal | None) -> Decimal:
        if change is None:
            return Decimal("45")
        move = abs(change)
        if move <= Decimal("2"):
            return Decimal("10")
        if move <= Decimal("5"):
            return Decimal("22")
        if move <= Decimal("10"):
            return Decimal("38")
        if move <= Decimal("20"):
            return Decimal("58")
        return Decimal("78")

    def score_all(self) -> int:
        count = 0
        with self.db.connect() as conn:
            model = conn.execute(
                """
                SELECT risk_model_id
                  FROM risk_models
                 WHERE model_name = 'NoRugs Core Risk Model'
                 ORDER BY created_at DESC
                 LIMIT 1
                """
            ).fetchone()
            if not model:
                raise RuntimeError("No active NoRugs risk model found")

            coins = conn.execute(
                "SELECT cryptocurrency_id FROM cryptocurrencies WHERE is_active = TRUE"
            ).fetchall()

            for coin in coins:
                market = conn.execute(
                    """
                    SELECT market_cap_usd, volume_24h_usd,
                           price_change_24h_pct, market_rank
                      FROM market_snapshots
                     WHERE cryptocurrency_id = %s
                     ORDER BY observed_at DESC
                     LIMIT 1
                    """,
                    (coin["cryptocurrency_id"],),
                ).fetchone()
                if not market:
                    continue

                cap = self.number(market["market_cap_usd"])
                volume = self.number(market["volume_24h_usd"])
                change = self.number(market["price_change_24h_pct"])
                rank = int(market["market_rank"]) if market["market_rank"] is not None else None

                factors = [
                    (
                        "Market Capitalization",
                        self.capitalization_score(cap),
                        Decimal("0.30"),
                        "Larger established market capitalization generally reduces manipulation and exit-risk concerns.",
                    ),
                    (
                        "Market Position",
                        self.rank_score(rank),
                        Decimal("0.25"),
                        f"The latest market rank is #{rank}." if rank is not None else "A current market rank is unavailable.",
                    ),
                    (
                        "Trading Activity",
                        self.activity_score(volume, cap),
                        Decimal("0.25"),
                        "This factor compares 24-hour trading volume with market capitalization.",
                    ),
                    (
                        "Price Volatility",
                        self.volatility_score(change),
                        Decimal("0.20"),
                        f"The latest 24-hour price movement is {change:.2f}%." if change is not None else "Current 24-hour movement is unavailable.",
                    ),
                ]

                overall = sum((score * weight for _, score, weight, _ in factors), Decimal("0"))
                overall = self.clamp(overall).quantize(Decimal("0.01"))
                level = "LOW" if overall < 25 else "MODERATE" if overall < 50 else "HIGH" if overall < 75 else "CRITICAL"

                available = sum(value is not None for value in (cap, volume, change, rank))
                confidence = (Decimal(available) / Decimal("4") * Decimal("100")).quantize(Decimal("0.01"))

                assessment = conn.execute(
                    """
                    INSERT INTO risk_assessments (
                        cryptocurrency_id, risk_model_id, overall_risk_score,
                        risk_level, confidence_score, summary
                    ) VALUES (%s, %s, %s, %s::risk_level, %s, %s)
                    RETURNING risk_assessment_id
                    """,
                    (
                        coin["cryptocurrency_id"],
                        model["risk_model_id"],
                        overall,
                        level,
                        confidence,
                        "Market-based screening using capitalization, rank, trading activity, and short-term volatility.",
                    ),
                ).fetchone()

                for name, score, weight, explanation in factors:
                    conn.execute(
                        """
                        INSERT INTO risk_factor_scores (
                            risk_assessment_id, factor_name, factor_score,
                            weight, weighted_score, explanation
                        ) VALUES (%s, %s, %s, %s, %s, %s)
                        """,
                        (
                            assessment["risk_assessment_id"],
                            name,
                            score,
                            weight,
                            score * weight,
                            explanation,
                        ),
                    )
                count += 1
        return count
