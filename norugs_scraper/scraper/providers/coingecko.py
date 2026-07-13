import os
from typing import Any

from dotenv import load_dotenv

from scraper.services.http_client import HttpClient

load_dotenv()


class CoinGeckoProvider:
    BASE_URL = "https://api.coingecko.com/api/v3"

    def __init__(self) -> None:
        self.api_key = os.getenv("COINGECKO_API_KEY")

    def _headers(self) -> dict[str, str]:
        if not self.api_key:
            return {}

        return {
            "x-cg-demo-api-key": self.api_key,
        }

    def get_coin(self, coin_id: str) -> dict[str, Any]:
        endpoint = f"{self.BASE_URL}/coins/{coin_id}"

        params = {
            "localization": "false",
            "tickers": "false",
            "market_data": "true",
            "community_data": "false",
            "developer_data": "false",
            "sparkline": "false",
        }

        with HttpClient() as http:
            result = http.get(
                endpoint,
                params=params,
                headers=self._headers(),
            )

        if not isinstance(result, dict):
            raise ValueError(
                "CoinGecko returned an unexpected coin response."
            )

        return result

    def get_market_page(
        self,
        page: int = 1,
        per_page: int = 250,
    ) -> list[dict[str, Any]]:
        endpoint = f"{self.BASE_URL}/coins/markets"

        params = {
            "vs_currency": "usd",
            "order": "market_cap_desc",
            "per_page": per_page,
            "page": page,
            "sparkline": "false",
            "price_change_percentage": "1h,24h,7d",
            "precision": "full",
        }

        with HttpClient() as http:
            result = http.get(
                endpoint,
                params=params,
                headers=self._headers(),
            )

        if not isinstance(result, list):
            raise ValueError(
                "CoinGecko returned an unexpected market response."
            )

        return result

    def get_top_markets(
        self,
        total_coins: int = 500,
    ) -> list[dict[str, Any]]:
        per_page = 250
        pages = (total_coins + per_page - 1) // per_page

        coins: list[dict[str, Any]] = []

        for page in range(1, pages + 1):
            page_data = self.get_market_page(
                page=page,
                per_page=per_page,
            )

            coins.extend(page_data)

            if len(page_data) < per_page:
                break

        return coins[:total_coins]