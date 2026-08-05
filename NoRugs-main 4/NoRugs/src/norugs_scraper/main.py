from __future__ import annotations

import argparse
import logging
from pathlib import Path

from norugs_scraper.collector import collect_once
from norugs_scraper.settings import Settings


def run() -> None:
    parser = argparse.ArgumentParser(description="Populate the NoRugs PostgreSQL database")
    parser.add_argument("--config", default="config/assets.json")
    parser.add_argument(
        "--provider",
        choices=["all", "coingecko", "dexscreener", "etherscan", "github", "risk"],
        default="all",
    )
    args = parser.parse_args()

    settings = Settings()
    logging.basicConfig(
        level=getattr(logging, settings.log_level.upper(), logging.INFO),
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    )
    results = collect_once(settings, Path(args.config), provider=args.provider)
    for provider, count in results.items():
        logging.getLogger("norugs").info("%s: stored/created %s records", provider, count)


if __name__ == "__main__":
    run()
