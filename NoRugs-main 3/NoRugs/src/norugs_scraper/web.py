from __future__ import annotations

import logging
import os
from decimal import Decimal
from pathlib import Path
from typing import Any

from flask import Flask, jsonify, send_from_directory
from psycopg import Connection
from psycopg.rows import dict_row

from norugs_scraper.live import LiveUpdateService
from norugs_scraper.settings import Settings

ROOT = Path(__file__).resolve().parents[2]
FRONTEND = ROOT / "frontend"
CONFIG_PATH = ROOT / "config" / "assets.json"

settings = Settings()
logging.basicConfig(
    level=getattr(logging, settings.log_level.upper(), logging.INFO),
    format="%(asctime)s %(levelname)s %(name)s: %(message)s",
)

app = Flask(__name__, static_folder=str(FRONTEND), static_url_path="")
live_updates = LiveUpdateService(
    settings,
    CONFIG_PATH,
    settings.live_update_interval_seconds,
)


def json_value(value: Any) -> Any:
    if isinstance(value, Decimal):
        return float(value)
    return value


def rows_to_json(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [{key: json_value(value) for key, value in row.items()} for row in rows]


def connect() -> Connection:
    return Connection.connect(settings.database_url, row_factory=dict_row)


@app.get("/")
def index():
    return send_from_directory(FRONTEND, "index.html")


@app.get("/<path:path>")
def frontend(path: str):
    candidate = FRONTEND / path
    if candidate.is_file():
        return send_from_directory(FRONTEND, path)
    return send_from_directory(FRONTEND, "index.html"), 404


@app.get("/api/health")
def health():
    update_status = live_updates.status()
    try:
        with connect() as conn:
            conn.execute("SELECT 1").fetchone()
        return jsonify({"status": "ok", "database": "connected", "updates": update_status})
    except Exception as exc:
        return jsonify({
            "status": "degraded",
            "database": "unavailable",
            "detail": str(exc),
            "updates": update_status,
        }), 503


@app.get("/api/updates/status")
def update_status():
    return jsonify(live_updates.status())


@app.post("/api/updates/refresh")
def refresh_now():
    accepted = live_updates.trigger()
    return jsonify({
        "accepted": accepted,
        "message": "Refresh started" if accepted else "A refresh is already running",
        "updates": live_updates.status(),
    }), 202 if accepted else 409


@app.get("/api/coins")
def coins():
    try:
        with connect() as conn:
            rows = conn.execute(
                """
                SELECT cryptocurrency_id, name, symbol, blockchain_name AS chain,
                       price_usd, price_change_24h_pct, market_cap_usd,
                       volume_24h_usd,
                       overall_risk_score, risk_level,
                       risk_assessed_at AS assessed_at,
                       market_data_updated_at, market_rank
                  FROM cryptocurrency_dashboard
                 ORDER BY market_rank NULLS LAST, name
                """
            ).fetchall()
        response = jsonify(rows_to_json(rows))
        response.headers["Cache-Control"] = "no-store"
        return response
    except Exception as exc:
        return jsonify({"error": "Unable to load coins", "detail": str(exc)}), 500


@app.get("/api/coins/<symbol>")
def coin(symbol: str):
    """Return one asset with the newest available evidence from every collector.

    The query is deliberately adaptive: fields that are not applicable to a coin
    remain null and the front end labels them honestly instead of using demo data.
    """
    try:
        with connect() as conn:
            row = conn.execute(
                """
                SELECT
                    c.cryptocurrency_id,
                    c.external_market_id,
                    c.name,
                    c.symbol,
                    c.contract_address,
                    c.website_url,
                    c.logo_url,
                    c.circulating_supply,
                    c.total_supply,
                    c.max_supply,
                    c.metadata,
                    b.name AS blockchain_name,
                    b.symbol AS blockchain_symbol,
                    m.price_usd,
                    m.market_cap_usd,
                    m.fully_diluted_valuation_usd,
                    m.volume_24h_usd,
                    m.price_change_1h_pct,
                    m.price_change_24h_pct,
                    m.price_change_7d_pct,
                    m.market_rank,
                    m.observed_at AS market_data_updated_at,
                    r.overall_risk_score,
                    r.risk_level,
                    r.confidence_score,
                    r.summary AS risk_summary,
                    r.assessed_at AS risk_assessed_at,
                    l.liquidity_usd,
                    l.dex_volume_24h_usd,
                    l.transactions_24h,
                    l.pool_count,
                    t.transaction_count_1h,
                    t.transaction_count_24h,
                    t.buy_count_24h,
                    t.sell_count_24h,
                    d.repository_count,
                    d.stars_count,
                    d.forks_count,
                    d.contributors_count,
                    d.commits_30d,
                    d.issues_open,
                    d.issues_closed_30d,
                    d.last_commit_at,
                    d.observed_at AS developer_data_updated_at,
                    h.holder_count,
                    h.top_1_pct,
                    h.top_5_pct,
                    h.top_10_pct,
                    h.top_20_pct,
                    h.developer_wallet_pct,
                    h.exchange_wallet_pct,
                    h.burn_wallet_pct,
                    h.observed_at AS holder_data_updated_at
                FROM cryptocurrencies c
                LEFT JOIN blockchains b ON b.blockchain_id = c.blockchain_id
                LEFT JOIN latest_market_data m ON m.cryptocurrency_id = c.cryptocurrency_id
                LEFT JOIN latest_risk_assessments r ON r.cryptocurrency_id = c.cryptocurrency_id
                LEFT JOIN LATERAL (
                    SELECT
                        SUM(ls.liquidity_usd) AS liquidity_usd,
                        SUM(ls.volume_24h_usd) AS dex_volume_24h_usd,
                        SUM(ls.transactions_24h) AS transactions_24h,
                        COUNT(DISTINCT lp.liquidity_pool_id) AS pool_count
                    FROM liquidity_pools lp
                    JOIN LATERAL (
                        SELECT x.* FROM liquidity_snapshots x
                        WHERE x.liquidity_pool_id = lp.liquidity_pool_id
                        ORDER BY x.observed_at DESC LIMIT 1
                    ) ls ON TRUE
                    WHERE lp.cryptocurrency_id = c.cryptocurrency_id
                ) l ON TRUE
                LEFT JOIN LATERAL (
                    SELECT tm.transaction_count_1h, tm.transaction_count_24h,
                           tm.buy_count_24h, tm.sell_count_24h
                    FROM transaction_metrics tm
                    WHERE tm.cryptocurrency_id = c.cryptocurrency_id
                    ORDER BY tm.observed_at DESC LIMIT 1
                ) t ON TRUE
                LEFT JOIN LATERAL (
                    SELECT da.repository_count, da.stars_count, da.forks_count,
                           da.contributors_count, da.commits_30d, da.issues_open,
                           da.issues_closed_30d, da.last_commit_at, da.observed_at
                    FROM developer_activity_snapshots da
                    WHERE da.cryptocurrency_id = c.cryptocurrency_id
                    ORDER BY da.observed_at DESC LIMIT 1
                ) d ON TRUE
                LEFT JOIN latest_concentration_data h
                       ON h.cryptocurrency_id = c.cryptocurrency_id
                WHERE UPPER(c.symbol) = UPPER(%s)
                ORDER BY m.observed_at DESC NULLS LAST
                LIMIT 1
                """,
                (symbol,),
            ).fetchone()
            if not row:
                return jsonify({
                    "error": "Coin not found",
                    "detail": (
                        f"No data for '{symbol}' yet. It may not be tracked in "
                        "config/assets.json, or the live collector hasn't scraped it "
                        "yet — try `norugs-scrape --provider all`."
                    ),
                }), 404

            factors = conn.execute(
                """
                SELECT rfs.factor_name, rfs.factor_score, rfs.weight,
                       rfs.weighted_score, rfs.explanation, rfs.evidence
                  FROM risk_factor_scores rfs
                  JOIN risk_assessments ra USING (risk_assessment_id)
                  JOIN cryptocurrencies c USING (cryptocurrency_id)
                 WHERE UPPER(c.symbol) = UPPER(%s)
                   AND ra.risk_assessment_id = (
                       SELECT ra2.risk_assessment_id
                         FROM risk_assessments ra2
                         JOIN cryptocurrencies c2 USING (cryptocurrency_id)
                        WHERE UPPER(c2.symbol) = UPPER(%s)
                        ORDER BY ra2.assessed_at DESC LIMIT 1
                   )
                 ORDER BY rfs.weight DESC
                """,
                (symbol, symbol),
            ).fetchall()

        payload = {key: json_value(value) for key, value in row.items()}
        payload["factors"] = rows_to_json(factors)
        payload["data_coverage"] = {
            "market": payload.get("price_usd") is not None,
            "liquidity": payload.get("liquidity_usd") is not None,
            "transactions": payload.get("transaction_count_24h") is not None,
            "developer": payload.get("developer_data_updated_at") is not None,
            "holders": payload.get("holder_data_updated_at") is not None,
            "contract": bool(payload.get("contract_address")),
        }
        response = jsonify(payload)
        response.headers["Cache-Control"] = "no-store"
        return response
    except Exception as exc:
        return jsonify({"error": "Unable to load coin", "detail": str(exc)}), 500


def start_live_updates() -> None:
    if settings.live_updates_enabled:
        live_updates.start(run_immediately=settings.live_update_on_start)


def run() -> None:
    port = int(os.getenv("PORT", "5000"))
    debug = os.getenv("FLASK_DEBUG") == "1"

    # Disable Flask's reloader so only one background collector is created.
    start_live_updates()
    app.run(host="127.0.0.1", port=port, debug=debug, use_reloader=False)


if __name__ == "__main__":
    run()
