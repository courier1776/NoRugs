# NoRugs Data Collector

This project populates the existing NoRugs PostgreSQL schema using official APIs rather than fragile HTML scraping.

## Providers

- **CoinGecko:** prices, market cap, supply, rank, and 1h/24h/7d changes.
- **DEX Screener:** DEX pools, liquidity, volume, and buy/sell counts.
- **Etherscan V2:** optional token-holder concentration. The top-holder endpoint may require a paid plan.
- **GitHub:** stars, forks, contributors, open issues, recent commits, and recently closed issues.
- **Risk engine:** creates a transparent starter assessment from available concentration, liquidity, and market activity data.

## 1. Open the project in VS Code

```bash
cd ~/Downloads/norugs_scraper
code .
```

## 2. Create and activate a virtual environment

```bash
python3 -m venv .venv
source .venv/bin/activate
```

## 3. Install

```bash
python -m pip install --upgrade pip
pip install -e .
```

## 4. Configure

```bash
cp .env.example .env
```

Your local Postgres.app values are already represented by:

```env
DB_HOST=localhost
DB_PORT=5433
DB_NAME=norugs
DB_USER=brendanwebb
DB_PASSWORD=
```

Add API keys to `.env` when available. Never commit `.env`.

Edit `config/assets.json` to choose coins, token contracts, and GitHub repositories. Load CoinGecko first because other providers link their records to those cryptocurrency rows.

## 5. Run

```bash
norugs-scrape --provider coingecko
norugs-scrape --provider dexscreener
norugs-scrape --provider github
norugs-scrape --provider risk
```

Or run everything:

```bash
norugs-scrape --provider all
```

## 6. Verify in psql

```sql
SELECT name, symbol, price_usd, market_cap_usd, overall_risk_score, risk_level
FROM cryptocurrency_dashboard
ORDER BY market_rank NULLS LAST;

SELECT source_id, status, started_at, completed_at, records_inserted, error_message
FROM scraper_runs
ORDER BY started_at DESC;
```

## Scheduling on macOS

For development, run manually first. Once stable, use `launchd` or a job scheduler to execute the command every 15–60 minutes. Do not poll more frequently than each provider's official rate limits permit.

## Important limitations

- A data feed is not proof that a coin is safe or fraudulent.
- Holder concentration must exclude known burn, exchange, liquidity, and contract wallets before it is treated as a reliable risk factor.
- DEX token symbols are not globally unique. For production, map assets by chain plus contract address rather than symbol.
- GitHub activity can be manipulated and should be treated as one supporting signal only.
- Respect API terms, authentication rules, and rate limits. Avoid scraping rendered website pages when a supported API exists.
