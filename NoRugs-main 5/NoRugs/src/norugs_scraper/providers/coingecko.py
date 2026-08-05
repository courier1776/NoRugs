from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from norugs_scraper.database import Database
from norugs_scraper.http import ApiClient
from norugs_scraper.settings import Settings


class CoinGeckoProvider:
    SOURCE_NAME = "CoinGecko"

    def __init__(self, settings: Settings, http: ApiClient, db: Database) -> None:
        self.settings = settings
        self.http = http
        self.db = db
        self.base_url = (
            "https://pro-api.coingecko.com/api/v3"
            if settings.coingecko_plan.lower() == "pro"
            else "https://api.coingecko.com/api/v3"
        )

    def _headers(self) -> dict[str, str]:
        if not self.settings.coingecko_api_key:
            return {}
        key_name = (
            "x-cg-pro-api-key"
            if self.settings.coingecko_plan.lower() == "pro"
            else "x-cg-demo-api-key"
        )
        return {key_name: self.settings.coingecko_api_key}

    def collect(self, coin_ids: list[str]) -> int:
        if not coin_ids:
            return 0

        endpoint = f"{self.base_url}/coins/markets"
        params: dict[str, object] = {
            "vs_currency": "usd",
            "ids": ",".join(coin_ids),
            "order": "market_cap_desc",
            "per_page": min(len(coin_ids), 250),
            "page": 1,
            "sparkline": "false",
            "price_change_percentage": "1h,24h,7d",
        }
        payload = self.http.get_json(endpoint, params=params, headers=self._headers())
        if not isinstance(payload, list):
            raise RuntimeError("CoinGecko returned an unexpected response")

        observed_at = datetime.now(timezone.utc)
        with self.db.connect() as conn:
            source_id = self.db.source_id(conn, self.SOURCE_NAME)
            run_id = self.db.start_run(conn, source_id, {"coin_ids": coin_ids})
            try:
                self.db.save_raw(
                    conn,
                    run_id=run_id,
                    source_id=source_id,
                    external_id=None,
                    request_url=endpoint,
                    payload=payload,
                )
                count = 0
                for item in payload:
                    if not isinstance(item, dict):
                        continue
                    crypto_id = self.db.upsert_crypto(
                        conn,
                        {
                            "external_market_id": item["id"],
                            "blockchain_name": None,
                            "name": item["name"],
                            "symbol": str(item["symbol"]).upper(),
                            "contract_address": None,
                            "website_url": None,
                            "logo_url": item.get("image"),
                            "circulating_supply": item.get("circulating_supply"),
                            "total_supply": item.get("total_supply"),
                            "max_supply": item.get("max_supply"),
                            "metadata": {"ath": item.get("ath"), "atl": item.get("atl")},
                        },
                    )
                    self.db.insert_market_snapshot(
                        conn,
                        cryptocurrency_id=crypto_id,
                        source_id=source_id,
                        item=item,
                        observed_at=observed_at,
                    )
                    count += 1
                self.db.finish_run(conn, run_id, "SUCCESS", found=len(payload), inserted=count)
                return count
            except Exception as exc:
                self.db.finish_run(conn, run_id, "FAILED", error=str(exc))
                raise
