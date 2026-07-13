import json
from typing import Any

from database.connection import get_database_connection


class CryptocurrencyRepository:
    def upsert_coin(self, coin: dict[str, Any]) -> int:
        query = """
        INSERT INTO cryptocurrencies (
            external_market_id,
            name,
            symbol,
            description,
            website_url,
            logo_url,
            total_supply,
            max_supply,
            circulating_supply,
            metadata
        )
        VALUES (
            %s, %s, %s, %s, %s,
            %s, %s, %s, %s, %s
        )
        ON CONFLICT (external_market_id)
        DO UPDATE SET
            name = EXCLUDED.name,
            symbol = EXCLUDED.symbol,
            description = EXCLUDED.description,
            website_url = EXCLUDED.website_url,
            logo_url = EXCLUDED.logo_url,
            total_supply = EXCLUDED.total_supply,
            max_supply = EXCLUDED.max_supply,
            circulating_supply = EXCLUDED.circulating_supply,
            metadata = EXCLUDED.metadata,
            updated_at = NOW()
        RETURNING cryptocurrency_id;
        """

        homepage = coin.get("links", {}).get("homepage", [])
        website_url = homepage[0] if homepage else None

        description = coin.get("description", {}).get("en")
        image = coin.get("image", {}).get("large")
        market_data = coin.get("market_data", {})

        values = (
            coin["id"],
            coin["name"],
            coin["symbol"].upper(),
            description,
            website_url,
            image,
            market_data.get("total_supply"),
            market_data.get("max_supply"),
            market_data.get("circulating_supply"),
            json.dumps(coin),
        )

        with get_database_connection() as connection:
            with connection.cursor() as cursor:
                cursor.execute(query, values)
                result = cursor.fetchone()

                if result is None:
                    raise RuntimeError("The cryptocurrency ID was not returned.")

                return result[0]