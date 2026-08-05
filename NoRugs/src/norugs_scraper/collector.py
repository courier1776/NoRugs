from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Any

from norugs_scraper.database import Database
from norugs_scraper.http import ApiClient
from norugs_scraper.providers.coingecko import CoinGeckoProvider
from norugs_scraper.providers.dexscreener import DexScreenerProvider
from norugs_scraper.providers.etherscan import EtherscanProvider
from norugs_scraper.providers.github import GitHubProvider
from norugs_scraper.risk import RiskScorer
from norugs_scraper.settings import Settings

LOG = logging.getLogger("norugs.collector")


def load_assets(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as file:
        data = json.load(file)
    if not isinstance(data, dict):
        raise ValueError("Asset configuration must be a JSON object")
    return data


def cap_assets(assets: dict[str, Any], max_tracked_assets: int) -> dict[str, Any]:
    """Truncate every tracked-asset list to at most max_tracked_assets entries.

    Keeps the app inside free/unauthenticated provider rate limits without
    requiring any API keys, no matter how large config/assets.json grows.
    """
    capped = dict(assets)
    for key in ("coingecko_ids", "dex_tokens", "etherscan_tokens", "github_repositories"):
        values = assets.get(key) or []
        if len(values) > max_tracked_assets:
            LOG.warning(
                "%s has %s entries; only the first %s will be collected "
                "(see MAX_TRACKED_ASSETS in .env)",
                key,
                len(values),
                max_tracked_assets,
            )
        capped[key] = values[:max_tracked_assets]
    return capped


def collect_once(
    settings: Settings,
    config_path: Path,
    *,
    provider: str = "all",
) -> dict[str, dict[str, Any]]:
    """Run one update cycle while isolating optional-provider failures.

    Returns a mapping of provider name -> {"count": int, "error": str | None}.
    A provider that raises is recorded as count=0 with its error message
    attached, rather than being indistinguishable from "nothing to collect".
    """
    assets = cap_assets(load_assets(config_path), settings.max_tracked_assets)
    db = Database(settings.database_url)
    http = ApiClient(settings.http_timeout_seconds)
    results: dict[str, dict[str, Any]] = {}

    def run_provider(name: str, callback) -> None:
        try:
            results[name] = {"count": callback(), "error": None}
        except Exception as exc:
            LOG.warning("%s update failed: %s", name, exc)
            results[name] = {"count": 0, "error": str(exc)}

    try:
        if provider in ("all", "coingecko"):
            run_provider(
                "coingecko",
                lambda: CoinGeckoProvider(settings, http, db).collect(
                    assets.get("coingecko_ids", [])
                ),
            )
        if provider in ("all", "dexscreener"):
            run_provider(
                "dexscreener",
                lambda: DexScreenerProvider(http, db).collect(
                    assets.get("dex_tokens", [])
                ),
            )
        if provider in ("all", "etherscan"):
            run_provider(
                "etherscan",
                lambda: EtherscanProvider(settings, http, db).collect(
                    assets.get("etherscan_tokens", [])
                ),
            )
        if provider in ("all", "github"):
            run_provider(
                "github",
                lambda: GitHubProvider(settings, http, db).collect(
                    assets.get("github_repositories", [])
                ),
            )
        if provider in ("all", "risk"):
            run_provider("risk", lambda: RiskScorer(db).score_all())
        return results
    finally:
        http.close()
