# NoRugs Complete Setup (macOS)

1. Make sure Postgres.app is running on port 5433.
2. Open this folder in VS Code.
3. In Terminal, run:

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -e .
cp .env.example .env
```

4. Confirm `.env` contains:

```env
DB_HOST=localhost
DB_PORT=5433
DB_NAME=norugs
DB_USER=brendanwebb
DB_PASSWORD=
LIVE_UPDATES_ENABLED=true
LIVE_UPDATE_INTERVAL_SECONDS=60
LIVE_UPDATE_ON_START=true
```

5. Start the complete application:

```bash
python run.py
```

6. Open:

- Dashboard: http://127.0.0.1:5000/dashboard.html
- Health: http://127.0.0.1:5000/api/health
- Update status: http://127.0.0.1:5000/api/updates/status

You may also double-click `START_NORUGS.command` after the first extraction.
