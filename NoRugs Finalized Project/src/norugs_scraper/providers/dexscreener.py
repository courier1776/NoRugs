from __future__ import annotations

from datetime import datetime, timezone

from norugs_scraper.database import Database
from norugs_scraper.http import ApiClient


class DexScreenerProvider:
    SOURCE_NAME = "DexScreener"
    BASE_URL = "https://api.dexscreener.com/latest/dex/tokens"

    def __init__(self, http: ApiClient, db: Database) -> None:
        self.http = http
        self.db = db

    def collect(self, tokens: list[dict[str, str]]) -> int:
        total = 0
        for token in tokens:
            total += self._collect_token(token["chain_id"], token["token_address"])
        return total

    def _collect_token(self, chain_id: str, token_address: str) -> int:
        endpoint = f"{self.BASE_URL}/{token_address}"
        payload = self.http.get_json(endpoint)
        if not isinstance(payload, dict):
            raise RuntimeError("DEX Screener returned an unexpected response")
        pairs = payload.get("pairs") or []
        observed_at = datetime.now(timezone.utc)

        with self.db.connect() as conn:
            source_id = self.db.source_id(conn, self.SOURCE_NAME)
            run_id = self.db.start_run(
                conn, source_id, {"chain_id": chain_id, "token_address": token_address}
            )
            try:
                self.db.save_raw(
                    conn,
                    run_id=run_id,
                    source_id=source_id,
                    external_id=token_address,
                    request_url=endpoint,
                    payload=payload,
                )
                count = 0
                for pair in pairs:
                    if str(pair.get("chainId", "")).lower() != chain_id.lower():
                        continue
                    base = pair.get("baseToken") or {}
                    quote = pair.get("quoteToken") or {}
                    # Match a token already loaded by CoinGecko using symbol first.
                    row = conn.execute(
                        """
                        SELECT cryptocurrency_id
                          FROM cryptocurrencies
                         WHERE UPPER(symbol) = UPPER(%s)
                         ORDER BY cryptocurrency_id
                         LIMIT 1
                        """,
                        (base.get("symbol"),),
                    ).fetchone()
                    if not row:
                        continue
                    crypto_id = int(row["cryptocurrency_id"])
                    exchange_id = self.db.upsert_exchange(
                        conn, str(pair.get("dexId") or "Unknown DEX")
                    )
                    blockchain_id = self.db.blockchain_id_by_symbolic_chain(conn, chain_id)
                    pool_id = self.db.upsert_liquidity_pool(
                        conn,
                        cryptocurrency_id=crypto_id,
                        blockchain_id=blockchain_id,
                        exchange_id=exchange_id,
                        pair_address=str(pair["pairAddress"]),
                        pair_symbol=f"{base.get('symbol', '?')}/{quote.get('symbol', '?')}",
                        paired_token_address=quote.get("address"),
                    )
                    self.db.insert_liquidity_snapshot(
                        conn,
                        pool_id=pool_id,
                        source_id=source_id,
                        pair=pair,
                        observed_at=observed_at,
                    )
                    self.db.insert_transaction_metrics(
                        conn,
                        cryptocurrency_id=crypto_id,
                        source_id=source_id,
                        pair=pair,
                        observed_at=observed_at,
                    )
                    count += 1
                self.db.finish_run(conn, run_id, "SUCCESS", found=len(pairs), inserted=count)
                return count
            except Exception as exc:
                self.db.finish_run(conn, run_id, "FAILED", error=str(exc))
                raise
