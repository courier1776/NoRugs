import json
from datetime import datetime, timezone
from typing import Any

from database.connection import get_database_connection


class BulkMarketRepository:
    def get_source_id(
        self,
        cursor,
        source_name: str = "CoinGecko",
    ) -> int:
        cursor.execute(
            """
            SELECT source_id
            FROM data_sources
            WHERE source_name = %s;
            """,
            (source_name,),
        )

        result = cursor.fetchone()

        if result is None:
            raise RuntimeError(
                f"{source_name} is missing from data_sources."
            )

        return result[0]

    def save_market_coin(
        self,
        cursor,
        source_id: int,
        coin: dict[str, Any],
        observed_at: datetime,
    ) -> int:
        coin_query = """
            INSERT INTO cryptocurrencies (
                external_market_id,
                name,
                symbol,
                logo_url,
                total_supply,
                max_supply,
                circulating_supply,
                metadata
            )
            VALUES (
                %s, %s, %s, %s,
                %s, %s, %s, %s
            )
            ON CONFLICT (external_market_id)
            DO UPDATE SET
                name = EXCLUDED.name,
                symbol = EXCLUDED.symbol,
                logo_url = EXCLUDED.logo_url,
                total_supply = EXCLUDED.total_supply,
                max_supply = EXCLUDED.max_supply,
                circulating_supply =
                    EXCLUDED.circulating_supply,
                metadata = EXCLUDED.metadata,
                updated_at = NOW()
            RETURNING cryptocurrency_id;
        """

        cursor.execute(
            coin_query,
            (
                coin["id"],
                coin["name"],
                coin["symbol"].upper(),
                coin.get("image"),
                coin.get("total_supply"),
                coin.get("max_supply"),
                coin.get("circulating_supply"),
                json.dumps(coin),
            ),
        )

        result = cursor.fetchone()

        if result is None:
            raise RuntimeError(
                f"Could not save {coin.get('id')}."
            )

        cryptocurrency_id = result[0]

        snapshot_query = """
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

        cursor.execute(
            snapshot_query,
            (
                cryptocurrency_id,
                source_id,
                coin.get("current_price"),
                coin.get("market_cap"),
                coin.get("fully_diluted_valuation"),
                coin.get("total_volume"),
                coin.get(
                    "price_change_percentage_1h_in_currency"
                ),
                coin.get(
                    "price_change_percentage_24h_in_currency",
                    coin.get("price_change_percentage_24h"),
                ),
                coin.get(
                    "price_change_percentage_7d_in_currency"
                ),
                coin.get("circulating_supply"),
                coin.get("total_supply"),
                coin.get("market_cap_rank"),
                observed_at,
            ),
        )

        return cryptocurrency_id

    def save_batch(
        self,
        coins: list[dict[str, Any]],
    ) -> list[int]:
        observed_at = datetime.now(timezone.utc)
        cryptocurrency_ids: list[int] = []

        with get_database_connection() as connection:
            with connection.cursor() as cursor:
                source_id = self.get_source_id(cursor)

                for coin in coins:
                    cryptocurrency_id = self.save_market_coin(
                        cursor=cursor,
                        source_id=source_id,
                        coin=coin,
                        observed_at=observed_at,
                    )

                    cryptocurrency_ids.append(
                        cryptocurrency_id
                    )

        return cryptocurrency_ids