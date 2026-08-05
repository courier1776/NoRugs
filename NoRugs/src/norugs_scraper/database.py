from __future__ import annotations

import hashlib
import json
from contextlib import contextmanager
from datetime import datetime
from decimal import Decimal
from typing import Any, Iterator

from psycopg import Connection
from psycopg.rows import dict_row


class Database:
    def __init__(self, database_url: str) -> None:
        self.database_url = database_url

    @contextmanager
    def connect(self) -> Iterator[Connection[dict[str, Any]]]:
        with Connection.connect(self.database_url, row_factory=dict_row) as conn:
            yield conn

    @staticmethod
    def source_id(conn: Connection, source_name: str) -> int:
        row = conn.execute(
            "SELECT source_id FROM data_sources WHERE source_name = %s",
            (source_name,),
        ).fetchone()
        if not row:
            raise RuntimeError(f"Missing data_sources row for {source_name}")
        return int(row["source_id"])

    @staticmethod
    def last_completed_at(conn: Connection, source_name: str) -> datetime | None:
        row = conn.execute(
            """
            SELECT MAX(sr.completed_at) AS last_completed_at
              FROM scraper_runs sr
              JOIN data_sources ds USING (source_id)
             WHERE ds.source_name = %s
               AND sr.completed_at IS NOT NULL
            """,
            (source_name,),
        ).fetchone()
        return row["last_completed_at"] if row else None

    @staticmethod
    def start_run(conn: Connection, source_id: int, metadata: dict[str, Any] | None = None) -> int:
        row = conn.execute(
            """
            INSERT INTO scraper_runs (source_id, status, metadata)
            VALUES (%s, 'RUNNING', %s::jsonb)
            RETURNING scraper_run_id
            """,
            (source_id, json.dumps(metadata or {})),
        ).fetchone()
        return int(row["scraper_run_id"])

    @staticmethod
    def finish_run(
        conn: Connection,
        run_id: int,
        status: str,
        *,
        found: int = 0,
        inserted: int = 0,
        updated: int = 0,
        error: str | None = None,
    ) -> None:
        conn.execute(
            """
            UPDATE scraper_runs
               SET status = %s::scrape_status,
                   completed_at = NOW(),
                   records_found = %s,
                   records_inserted = %s,
                   records_updated = %s,
                   error_message = %s
             WHERE scraper_run_id = %s
            """,
            (status, found, inserted, updated, error, run_id),
        )

    @staticmethod
    def save_raw(
        conn: Connection,
        *,
        run_id: int,
        source_id: int,
        external_id: str | None,
        request_url: str,
        payload: object,
    ) -> None:
        encoded = json.dumps(payload, sort_keys=True, separators=(",", ":"), default=str)
        payload_hash = hashlib.sha256(encoded.encode("utf-8")).hexdigest()
        conn.execute(
            """
            INSERT INTO raw_scraped_data
                (scraper_run_id, source_id, external_id, request_url, payload, payload_hash)
            VALUES (%s, %s, %s, %s, %s::jsonb, %s)
            ON CONFLICT DO NOTHING
            """,
            (run_id, source_id, external_id, request_url, encoded, payload_hash),
        )

    @staticmethod
    def upsert_crypto(conn: Connection, coin: dict[str, Any]) -> int:
        row = conn.execute(
            """
            INSERT INTO cryptocurrencies (
                external_market_id, blockchain_id, name, symbol, contract_address,
                website_url, logo_url, circulating_supply, total_supply, max_supply,
                metadata
            )
            VALUES (
                %(external_market_id)s,
                (SELECT blockchain_id FROM blockchains WHERE name = %(blockchain_name)s),
                %(name)s, %(symbol)s, %(contract_address)s, %(website_url)s,
                %(logo_url)s, %(circulating_supply)s, %(total_supply)s, %(max_supply)s,
                %(metadata)s::jsonb
            )
            ON CONFLICT (external_market_id) DO UPDATE SET
                name = EXCLUDED.name,
                symbol = EXCLUDED.symbol,
                logo_url = COALESCE(EXCLUDED.logo_url, cryptocurrencies.logo_url),
                circulating_supply = EXCLUDED.circulating_supply,
                total_supply = EXCLUDED.total_supply,
                max_supply = EXCLUDED.max_supply,
                metadata = cryptocurrencies.metadata || EXCLUDED.metadata,
                updated_at = NOW()
            RETURNING cryptocurrency_id
            """,
            {
                **coin,
                "metadata": json.dumps(coin.get("metadata", {})),
            },
        ).fetchone()
        return int(row["cryptocurrency_id"])

    @staticmethod
    def crypto_id_by_external(conn: Connection, external_id: str) -> int | None:
        row = conn.execute(
            "SELECT cryptocurrency_id FROM cryptocurrencies WHERE external_market_id = %s",
            (external_id,),
        ).fetchone()
        return int(row["cryptocurrency_id"]) if row else None

    @staticmethod
    def insert_market_snapshot(
        conn: Connection,
        *,
        cryptocurrency_id: int,
        source_id: int,
        item: dict[str, Any],
        observed_at: datetime,
    ) -> None:
        conn.execute(
            """
            INSERT INTO market_snapshots (
                cryptocurrency_id, source_id, price_usd, market_cap_usd,
                fully_diluted_valuation_usd, volume_24h_usd,
                price_change_1h_pct, price_change_24h_pct, price_change_7d_pct,
                circulating_supply, total_supply, market_rank, observed_at
            ) VALUES (
                %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s
            )
            ON CONFLICT DO NOTHING
            """,
            (
                cryptocurrency_id,
                source_id,
                item.get("current_price"),
                item.get("market_cap"),
                item.get("fully_diluted_valuation"),
                item.get("total_volume"),
                item.get("price_change_percentage_1h_in_currency"),
                item.get("price_change_percentage_24h"),
                item.get("price_change_percentage_7d_in_currency"),
                item.get("circulating_supply"),
                item.get("total_supply"),
                item.get("market_cap_rank"),
                observed_at,
            ),
        )

    @staticmethod
    def upsert_exchange(conn: Connection, name: str, exchange_type: str = "DEX") -> int:
        row = conn.execute(
            """
            INSERT INTO exchanges (name, exchange_type)
            VALUES (%s, %s)
            ON CONFLICT (name) DO UPDATE SET is_active = TRUE
            RETURNING exchange_id
            """,
            (name, exchange_type),
        ).fetchone()
        return int(row["exchange_id"])

    @staticmethod
    def blockchain_id_by_symbolic_chain(conn: Connection, chain_id: str) -> int | None:
        aliases = {
            "ethereum": "Ethereum",
            "bsc": "BNB Smart Chain",
            "binance-smart-chain": "BNB Smart Chain",
            "solana": "Solana",
            "polygon": "Polygon",
        }
        name = aliases.get(chain_id.lower())
        if not name:
            return None
        row = conn.execute(
            "SELECT blockchain_id FROM blockchains WHERE name = %s", (name,)
        ).fetchone()
        return int(row["blockchain_id"]) if row else None

    @staticmethod
    def upsert_liquidity_pool(
        conn: Connection,
        *,
        cryptocurrency_id: int,
        blockchain_id: int | None,
        exchange_id: int,
        pair_address: str,
        pair_symbol: str,
        paired_token_address: str | None,
    ) -> int:
        row = conn.execute(
            """
            INSERT INTO liquidity_pools (
                cryptocurrency_id, blockchain_id, exchange_id, pool_address,
                pair_symbol, paired_token_address
            ) VALUES (%s, %s, %s, %s, %s, %s)
            ON CONFLICT (blockchain_id, LOWER(pool_address)) DO UPDATE SET
                exchange_id = EXCLUDED.exchange_id,
                pair_symbol = EXCLUDED.pair_symbol,
                paired_token_address = EXCLUDED.paired_token_address
            RETURNING liquidity_pool_id
            """,
            (
                cryptocurrency_id,
                blockchain_id,
                exchange_id,
                pair_address,
                pair_symbol,
                paired_token_address,
            ),
        ).fetchone()
        return int(row["liquidity_pool_id"])

    @staticmethod
    def insert_liquidity_snapshot(
        conn: Connection,
        *,
        pool_id: int,
        source_id: int,
        pair: dict[str, Any],
        observed_at: datetime,
    ) -> None:
        txns = pair.get("txns", {}).get("h24", {}) or {}
        conn.execute(
            """
            INSERT INTO liquidity_snapshots (
                liquidity_pool_id, source_id, liquidity_usd, volume_24h_usd,
                transactions_24h, observed_at
            ) VALUES (%s, %s, %s, %s, %s, %s)
            ON CONFLICT DO NOTHING
            """,
            (
                pool_id,
                source_id,
                (pair.get("liquidity") or {}).get("usd"),
                (pair.get("volume") or {}).get("h24"),
                int(txns.get("buys", 0) or 0) + int(txns.get("sells", 0) or 0),
                observed_at,
            ),
        )

    @staticmethod
    def insert_transaction_metrics(
        conn: Connection,
        *,
        cryptocurrency_id: int,
        source_id: int,
        pair: dict[str, Any],
        observed_at: datetime,
    ) -> None:
        txns = pair.get("txns", {}) or {}
        h1 = txns.get("h1", {}) or {}
        h24 = txns.get("h24", {}) or {}
        conn.execute(
            """
            INSERT INTO transaction_metrics (
                cryptocurrency_id, source_id, transaction_count_1h,
                transaction_count_24h, buy_count_24h, sell_count_24h,
                observed_at
            ) VALUES (%s, %s, %s, %s, %s, %s, %s)
            ON CONFLICT DO NOTHING
            """,
            (
                cryptocurrency_id,
                source_id,
                int(h1.get("buys", 0) or 0) + int(h1.get("sells", 0) or 0),
                int(h24.get("buys", 0) or 0) + int(h24.get("sells", 0) or 0),
                int(h24.get("buys", 0) or 0),
                int(h24.get("sells", 0) or 0),
                observed_at,
            ),
        )

    @staticmethod
    def insert_developer_snapshot(
        conn: Connection,
        *,
        cryptocurrency_id: int,
        source_id: int,
        data: dict[str, Any],
        observed_at: datetime,
    ) -> None:
        conn.execute(
            """
            INSERT INTO developer_activity_snapshots (
                cryptocurrency_id, source_id, repository_count, stars_count,
                forks_count, contributors_count, commits_30d, issues_open,
                issues_closed_30d, last_commit_at, observed_at
            ) VALUES (%s, %s, 1, %s, %s, %s, %s, %s, %s, %s, %s)
            ON CONFLICT DO NOTHING
            """,
            (
                cryptocurrency_id,
                source_id,
                data.get("stars_count"),
                data.get("forks_count"),
                data.get("contributors_count"),
                data.get("commits_30d"),
                data.get("issues_open"),
                data.get("issues_closed_30d"),
                data.get("last_commit_at"),
                observed_at,
            ),
        )
