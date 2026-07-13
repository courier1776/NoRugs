from datetime import datetime, timezone
from typing import Any

from database.connection import get_database_connection


class MarketRepository:
    def get_coingecko_source_id(self) -> int:
        query = """
        SELECT source_id
        FROM data_sources
        WHERE source_name = 'CoinGecko';
        """

        with get_database_connection() as connection:
            with connection.cursor() as cursor:
                cursor.execute(query)
                result = cursor.fetchone()

                if result is None:
                    raise RuntimeError(
                        "CoinGecko is missing from the data_sources table."
                    )

                return result[0]

    def insert_snapshot(
        self,
        cryptocurrency_id: int,
        coin: dict[str, Any],
    ) -> None:
        market_data = coin.get("market_data", {})
        current_price = market_data.get("current_price", {})
        market_cap = market_data.get("market_cap", {})
        volume = market_data.get("total_volume", {})
        fdv = market_data.get("fully_diluted_valuation", {})

        query = """
        INSERT INTO market_snapshots (
            cryptocurrency_id,
            source_id,
            price_usd,
            market_cap_usd,
            fully_diluted_valuation_usd,
            volume_24h_usd,
            price_change_1h_pct,
            price_change_24h_pct,
            price_change_7d_pct,
            circulating_supply,
            total_supply,
            market_rank,
            observed_at
        )
        VALUES (
            %s, %s, %s, %s, %s,
            %s, %s, %s, %s, %s,
            %s, %s, %s
        );
        """

        values = (
            cryptocurrency_id,
            self.get_coingecko_source_id(),
            current_price.get("usd"),
            market_cap.get("usd"),
            fdv.get("usd"),
            volume.get("usd"),
            market_data.get("price_change_percentage_1h_in_currency", {}).get(
                "usd"
            ),
            market_data.get("price_change_percentage_24h"),
            market_data.get("price_change_percentage_7d"),
            market_data.get("circulating_supply"),
            market_data.get("total_supply"),
            coin.get("market_cap_rank"),
            datetime.now(timezone.utc),
        )

        with get_database_connection() as connection:
            with connection.cursor() as cursor:
                cursor.execute(query, values)