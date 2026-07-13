from fastapi import APIRouter, HTTPException, Query
from psycopg2.extras import RealDictCursor

from api.schemas import CoinDetail, CoinSummary, RiskFactor
from database.connection import get_database_connection


router = APIRouter(
    prefix="/api/coins",
    tags=["coins"],
)


@router.get("", response_model=list[CoinSummary])
def get_coins(
    search: str | None = Query(default=None, max_length=100),
    risk_level: str | None = Query(default=None),
    limit: int = Query(default=100, ge=1, le=500),
) -> list[dict]:
    conditions: list[str] = []
    parameters: list[object] = []

    if search:
        conditions.append(
            "("
            "dashboard.name ILIKE %s "
            "OR dashboard.symbol ILIKE %s "
            "OR crypto.external_market_id ILIKE %s"
            ")"
        )

        search_term = f"%{search}%"
        parameters.extend(
            [
                search_term,
                search_term,
                search_term,
            ]
        )

    if risk_level:
        conditions.append(
            "dashboard.risk_level::text = %s"
        )
        parameters.append(risk_level.upper())

    where_clause = ""

    if conditions:
        where_clause = "WHERE " + " AND ".join(conditions)

    query = f"""
        SELECT
            dashboard.cryptocurrency_id,
            crypto.external_market_id,
            dashboard.name,
            dashboard.symbol,
            dashboard.logo_url,
            dashboard.price_usd,
            dashboard.market_cap_usd,
            dashboard.volume_24h_usd,
            dashboard.price_change_24h_pct,
            dashboard.market_rank,
            dashboard.overall_risk_score,
            dashboard.risk_level::text AS risk_level,
            dashboard.confidence_score,
            dashboard.risk_summary,
            dashboard.market_data_updated_at,
            dashboard.risk_assessed_at
        FROM cryptocurrency_dashboard dashboard
        JOIN cryptocurrencies crypto
            ON crypto.cryptocurrency_id =
               dashboard.cryptocurrency_id
        {where_clause}
        ORDER BY
            dashboard.market_rank NULLS LAST,
            dashboard.market_cap_usd DESC NULLS LAST
        LIMIT %s;
    """

    parameters.append(limit)

    with get_database_connection() as connection:
        with connection.cursor(
            cursor_factory=RealDictCursor
        ) as cursor:
            cursor.execute(query, parameters)
            return list(cursor.fetchall())


@router.get("/{coin_id}", response_model=CoinDetail)
def get_coin(coin_id: str) -> dict:
    coin_query = """
        SELECT
            dashboard.cryptocurrency_id,
            crypto.external_market_id,
            dashboard.name,
            dashboard.symbol,
            dashboard.logo_url,
            dashboard.price_usd,
            dashboard.market_cap_usd,
            dashboard.volume_24h_usd,
            dashboard.price_change_24h_pct,
            dashboard.market_rank,
            dashboard.overall_risk_score,
            dashboard.risk_level::text AS risk_level,
            dashboard.confidence_score,
            dashboard.risk_summary,
            dashboard.market_data_updated_at,
            dashboard.risk_assessed_at,
            crypto.description,
            crypto.website_url,
            crypto.circulating_supply,
            crypto.total_supply,
            crypto.max_supply,
            latest_risk.risk_assessment_id
        FROM cryptocurrency_dashboard dashboard
        JOIN cryptocurrencies crypto
            ON crypto.cryptocurrency_id =
               dashboard.cryptocurrency_id
        LEFT JOIN latest_risk_assessments latest_risk
            ON latest_risk.cryptocurrency_id =
               dashboard.cryptocurrency_id
        WHERE
            crypto.external_market_id = %s
            OR dashboard.cryptocurrency_id::text = %s
        LIMIT 1;
    """

    factor_query = """
        SELECT
            factor_name,
            factor_score,
            weight,
            weighted_score,
            explanation,
            evidence
        FROM risk_factor_scores
        WHERE risk_assessment_id = %s
        ORDER BY
            weighted_score DESC NULLS LAST,
            factor_name ASC;
    """

    with get_database_connection() as connection:
        with connection.cursor(
            cursor_factory=RealDictCursor
        ) as cursor:
            cursor.execute(
                coin_query,
                (
                    coin_id,
                    coin_id,
                ),
            )

            coin = cursor.fetchone()

            if coin is None:
                raise HTTPException(
                    status_code=404,
                    detail="Cryptocurrency not found.",
                )

            assessment_id = coin.pop(
                "risk_assessment_id",
                None,
            )

            coin["risk_factors"] = []

            if assessment_id is not None:
                cursor.execute(
                    factor_query,
                    (assessment_id,),
                )

                coin["risk_factors"] = [
                    RiskFactor(**row)
                    for row in cursor.fetchall()
                ]

            return coin