from database.repositories.bulk_market_repository import (
    BulkMarketRepository,
)
from database.repositories.risk_repository import RiskRepository
from risk_engine.scorer import calculate_market_risk
from scraper.providers.coingecko import CoinGeckoProvider


TOTAL_COINS = 500


def main() -> None:
    provider = CoinGeckoProvider()
    market_repository = BulkMarketRepository()
    risk_repository = RiskRepository()

    print(
        f"Downloading the top {TOTAL_COINS} "
        "cryptocurrencies..."
    )

    coins = provider.get_top_markets(
        total_coins=TOTAL_COINS
    )

    print(f"Received {len(coins)} records.")

    cryptocurrency_ids = market_repository.save_batch(
        coins
    )

    saved_assessments = 0
    failed_assessments = 0

    for cryptocurrency_id, coin in zip(
        cryptocurrency_ids,
        coins,
    ):
        try:
            risk_result = calculate_market_risk(coin)

            risk_repository.save_assessment(
                cryptocurrency_id,
                risk_result,
            )

            saved_assessments += 1

            print(
                f"{coin['name']}: "
                f"{risk_result.overall_score}/100 "
                f"({risk_result.risk_level})"
            )

        except Exception as error:
            failed_assessments += 1

            print(
                f"Risk assessment failed for "
                f"{coin.get('id')}: {error}"
            )

    print()
    print("Collection completed.")
    print(f"Cryptocurrencies saved: {len(coins)}")
    print(f"Risk assessments saved: {saved_assessments}")
    print(f"Risk failures: {failed_assessments}")


if __name__ == "__main__":
    main()