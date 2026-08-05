from __future__ import annotations

from datetime import datetime, timezone
from decimal import Decimal

from norugs_scraper.database import Database
from norugs_scraper.http import ApiClient
from norugs_scraper.settings import Settings


class EtherscanProvider:
    """Optional holder collector.

    The top-holder endpoint may require a paid Etherscan plan. Configure only
    tokens and chains supported by your account.
    """

    SOURCE_NAME = "Etherscan"
    ENDPOINT = "https://api.etherscan.io/v2/api"

    def __init__(self, settings: Settings, http: ApiClient, db: Database) -> None:
        self.settings = settings
        self.http = http
        self.db = db

    def collect(self, tokens: list[dict[str, str]]) -> int:
        if not self.settings.etherscan_api_key or not tokens:
            return 0
        return sum(self._collect_token(item) for item in tokens)

    def _collect_token(self, item: dict[str, str]) -> int:
        params = {
            "chainid": item.get("chain_id", "1"),
            "module": "token",
            "action": "topholders",
            "contractaddress": item["contract_address"],
            "offset": int(item.get("offset", "100")),
            "apikey": self.settings.etherscan_api_key,
        }
        payload = self.http.get_json(self.ENDPOINT, params=params)
        if not isinstance(payload, dict) or str(payload.get("status")) != "1":
            raise RuntimeError(f"Etherscan error: {payload}")
        holders = payload.get("result") or []
        observed_at = datetime.now(timezone.utc)

        with self.db.connect() as conn:
            source_id = self.db.source_id(conn, self.SOURCE_NAME)
            run_id = self.db.start_run(conn, source_id, item)
            try:
                self.db.save_raw(
                    conn,
                    run_id=run_id,
                    source_id=source_id,
                    external_id=item["contract_address"],
                    request_url=self.ENDPOINT,
                    payload=payload,
                )
                crypto_id = self.db.crypto_id_by_external(conn, item["coingecko_id"])
                if crypto_id is None:
                    raise RuntimeError("Cryptocurrency must be loaded from CoinGecko first")
                blockchain_id = self.db.blockchain_id_by_symbolic_chain(conn, item.get("chain", "ethereum"))
                if blockchain_id is None:
                    raise RuntimeError("Unknown blockchain mapping")

                total_supply = Decimal(str(item["total_supply"]))
                percentages: list[Decimal] = []
                for rank, holder in enumerate(holders, start=1):
                    address = holder.get("TokenHolderAddress") or holder.get("address")
                    balance = Decimal(str(holder.get("TokenHolderQuantity") or holder.get("value") or 0))
                    pct = (balance / total_supply * Decimal("100")) if total_supply else Decimal("0")
                    percentages.append(pct)
                    wallet = conn.execute(
                        """
                        INSERT INTO wallets (blockchain_id, wallet_address)
                        VALUES (%s, %s)
                        ON CONFLICT (blockchain_id, LOWER(wallet_address)) DO UPDATE SET updated_at = NOW()
                        RETURNING wallet_id
                        """,
                        (blockchain_id, address),
                    ).fetchone()
                    conn.execute(
                        """
                        INSERT INTO holder_snapshots (
                            cryptocurrency_id, wallet_id, source_id, token_balance,
                            ownership_pct, holder_rank, observed_at
                        ) VALUES (%s, %s, %s, %s, %s, %s, %s)
                        ON CONFLICT DO NOTHING
                        """,
                        (crypto_id, wallet["wallet_id"], source_id, balance, pct, rank, observed_at),
                    )

                def top(n: int) -> Decimal:
                    return sum(percentages[:n], Decimal("0"))

                conn.execute(
                    """
                    INSERT INTO concentration_snapshots (
                        cryptocurrency_id, source_id, holder_count, top_1_pct,
                        top_5_pct, top_10_pct, top_20_pct, observed_at
                    ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                    ON CONFLICT DO NOTHING
                    """,
                    (crypto_id, source_id, len(holders), top(1), top(5), top(10), top(20), observed_at),
                )
                self.db.finish_run(conn, run_id, "SUCCESS", found=len(holders), inserted=len(holders))
                return len(holders)
            except Exception as exc:
                self.db.finish_run(conn, run_id, "FAILED", error=str(exc))
                raise
