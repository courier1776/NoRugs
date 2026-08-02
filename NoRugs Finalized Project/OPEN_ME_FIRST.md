# NoRugs Simplified Live Edition

This edition focuses on reliable live market fields and removes empty wallet, contract, and liquidity panels from the coin-analysis page.

## Start on macOS

1. Start Postgres.app.
2. Open this folder in VS Code.
3. Open **Terminal > New Terminal**.
4. Run:

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -e .
cp .env.example .env
python run.py
```


Open:

- Dashboard: http://127.0.0.1:5000/dashboard.html


## New scoring model

The live score uses four consistently available categories:

- Market capitalization
- Market rank
- 24-hour volume relative to market capitalization
- 24-hour price volatility

Higher scores mean higher preliminary market risk. The score is not financial advice or a guarantee.
