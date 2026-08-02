# NoRugs Integrated Project

This package combines the redesigned NoRugs front end, Flask API server, PostgreSQL schema, data collectors, and risk-scoring engine.

Start with **`START_HERE.md`** for complete macOS setup instructions.

## Main folders

- `frontend/` — HTML, CSS, and JavaScript interface
- `src/norugs_scraper/` — Flask server, collectors, database integration, and risk engine
- `database/schema.sql` — PostgreSQL database schema
- `config/assets.json` — configured assets and repositories

## Quick start after initial setup

```bash
cd NoRugs_Integrated
source .venv/bin/activate
norugs-web
```

Open `http://127.0.0.1:5000/dashboard.html`.

## Continuous live updates

When `norugs-web` starts, a background service now refreshes provider data and recalculates risk scores automatically. The default database refresh interval is 60 seconds, and the dashboard requests fresh API data every 15 seconds while its browser tab is visible.

Configure the behavior in `.env`:

```env
LIVE_UPDATES_ENABLED=true
LIVE_UPDATE_INTERVAL_SECONDS=60
LIVE_UPDATE_ON_START=true
```

The minimum supported database update interval is 15 seconds. A longer interval may be necessary for free API plans and rate limits.

Status endpoints:

- `GET /api/updates/status` — current scheduler state and last result
- `POST /api/updates/refresh` — request an immediate refresh
- `GET /api/health` — database and updater health

The scheduler prevents overlapping refresh cycles and catches provider/database errors so a failed update does not stop the Flask server.


## Interactive pages
Portfolio Analysis, Compare, Watchlist, and Alerts now use the live `/api/coins` data. Portfolio holdings, watchlists, and alert rules are stored locally in the browser and refresh every 15 seconds.
