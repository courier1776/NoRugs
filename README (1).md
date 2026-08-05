# NoRugs — Setup Guide

This guide walks through everything needed to go from a brand-new computer with **no software installed** to the NoRugs cryptocurrency risk dashboard running in your browser. It covers **Windows** and **macOS** side by side — follow the column for your operating system at each step. No prior experience with Python, PostgreSQL, or the command line is assumed.

By the end, you will have:

- Python and PostgreSQL installed
- The NoRugs project downloaded and its dependencies installed
- A local `norugs` database, created and loaded with the project's schema
- The Flask application running at `http://127.0.0.1:5000`, collecting live market data in the background

Estimated time: **30–45 minutes**.

---

## What you'll install

| Software | Why it's needed | Download |
|---|---|---|
| Python 3.11 or newer | Runs the backend server and data collector | https://python.org/downloads |
| PostgreSQL 14 or newer (with pgAdmin 4) | Stores all tracked assets, prices, and risk scores | https://www.postgresql.org/download |
| A code editor (recommended: VS Code) | Makes editing `.env` and running terminal commands easier | https://code.visualstudio.com |
| Git (optional) | Only needed if you clone the repo instead of downloading a ZIP | https://git-scm.com/downloads |

Node.js is **not** required — the frontend is plain HTML/CSS/JavaScript with no build step.

---

## Step 1 — Install Python

### Windows
1. Go to https://python.org/downloads and download the latest **Python 3.x** installer.
2. Run the installer. On the first screen, check the box **"Add python.exe to PATH"** — it's a good habit, but don't worry if you miss it, because the next step doesn't depend on it.
3. When it finishes, open **Command Prompt** and confirm the install using the **`py` launcher**, not `python`:
   ```bat
   py --version
   ```
   You should see `Python 3.11` or higher.

   The Windows installer always registers `py` on your system PATH automatically, whether or not you checked the PATH box above — that's why this guide uses `py` for every Windows command instead of `python`, which only works if that box was checked. (If you'd rather use `python`, that's fine too as long as `python --version` actually works — just substitute it anywhere this guide says `py`.)

### macOS
1. Go to https://python.org/downloads and download the macOS installer (or run `brew install python3` if you already use Homebrew).
2. Run the installer package and follow the prompts.
3. Open **Terminal** (Applications → Utilities → Terminal) and confirm:
   ```bash
   python3 --version
   ```
   You should see `Python 3.11` or higher.

> Commands differ by OS throughout this guide: Windows uses `py`, macOS uses `python3`. Once you activate the project's virtual environment in Step 6, both platforms switch to plain `python` for every command after that — the venv takes care of pointing it at the right interpreter.

---

## Step 2 — Install PostgreSQL

1. Go to https://www.postgresql.org/download and choose your operating system.
2. Run the installer. When prompted:
   - Leave the **port** as the default, **5432**.
   - Set and **remember a password** for the `postgres` superuser account — you'll need it shortly.
   - Make sure **pgAdmin 4** is included in the install (it's checked by default).
3. Let the installer finish, then open **pgAdmin 4** from your Start Menu / Applications folder.
4. In pgAdmin, expand **Servers → PostgreSQL** in the left sidebar and enter the password you just set. If it connects without an error, PostgreSQL is running correctly.

> macOS users who prefer **Postgres.app** instead of the installer above can use that — just note its default port is often **5433**, not 5432. Whichever port your server actually uses is the one you'll put in the `.env` file in Step 9.

---

## Step 3 — Install VS Code

VS Code is the editor you'll use to open the project folder, edit the `.env` configuration file, and run all the terminal commands in this guide.

### Windows
1. Go to https://code.visualstudio.com and click **Download for Windows**.
2. Run the installer. On the "Select Additional Tasks" screen, it's worth checking **"Add to PATH"** and **"Add 'Open with Code' action"** — both are checked by default and make VS Code easier to launch later.
3. Finish the install, then open VS Code from the Start Menu to confirm it launches.

### macOS
1. Go to https://code.visualstudio.com and click **Download for Mac**.
2. Open the downloaded `.zip` file — it will expand into a **Visual Studio Code** application.
3. Drag **Visual Studio Code** into your **Applications** folder.
4. Open it from Applications (the first time, macOS may ask you to confirm you want to open an app downloaded from the internet — click **Open**).

You don't need to sign in or create an account — VS Code opens straight to a usable editor.

---

## Step 4 — Get the project files

**Option A — Download the ZIP** (simplest, no Git required)
1. Download the NoRugs project ZIP file.
2. Extract it somewhere easy to find, such as your Documents folder.
3. Rename the extracted folder to `NoRugs` if it isn't already, for simplicity.

**Option B — Clone with Git**
```bash
git clone https://github.com/<your-username>/NoRugs.git
cd NoRugs
```

---

## Step 5 — Open the project

1. Open **VS Code**.
2. **File → Open Folder** and select the `NoRugs` folder from Step 4.
3. Open a terminal inside VS Code: **Terminal → New Terminal**.

Every command from here on should be run from this terminal, from inside the `NoRugs` folder.

---

## Step 6 — Create a virtual environment

A virtual environment keeps this project's Python packages separate from everything else on your computer.

### Windows
```bat
py -m venv .venv
.venv\Scripts\activate
```

### macOS
```bash
python3 -m venv .venv
source .venv/bin/activate
```

After activating, your terminal prompt should now begin with `(.venv)`. From this point on, both Windows and macOS use plain `python` (not `py` or `python3`) for every remaining command in this guide — activating the environment points `python` at the right interpreter automatically. Run every command below with the environment active — if you close and reopen your terminal later, just re-run the activate command above before continuing.

---

## Step 7 — Install the project's dependencies

With the virtual environment active:

```bash
python -m pip install --upgrade pip
python -m pip install -e .
```

This reads `pyproject.toml` and installs everything the project needs (Flask, httpx, psycopg, pydantic-settings, tenacity, and python-dotenv), and also registers two convenience commands you'll use later: `norugs-web` and `norugs-scrape`.

> If this step fails for any reason, `python -m pip install -r requirements.txt` installs the same dependencies without registering those two commands — in that case, use `python run.py` instead of `norugs-web` in the steps below.

---

## Step 8 — Create the database

1. Open **pgAdmin 4**.
2. Right-click **Databases → Create → Database…**
3. Name it exactly:
   ```
   norugs
   ```
4. Click **Save**.

---

## Step 9 — Load the database schema

The project ships a complete schema (over twenty tables) in `database/schema.sql`. Load it one of two ways:

**Option A — pgAdmin (no command line)**
1. Right-click the new `norugs` database → **Query Tool**.
2. Click the folder icon and open `database/schema.sql` from the project folder.
3. Click the ▶ **Execute** button (or press F5).
4. You should see "Query returned successfully" with no errors.

**Option B — Terminal**
```bash
psql -U postgres -d norugs -f database/schema.sql
```
Enter your PostgreSQL password when prompted. (On Windows, `psql` must be on your PATH — the PostgreSQL installer adds it, but you may need to open a **new** Command Prompt window after installing for it to be recognized.)

---

## Step 10 — Configure the connection (`.env` file)

The application reads its configuration from a file named `.env` in the project's root folder. This file does not exist yet — create it now.

1. In VS Code, right-click the project folder → **New File** → name it exactly `.env`.
2. Paste in the following, replacing the placeholders with the values from Step 2:

   ```env
   DB_HOST=localhost
   DB_PORT=5432
   DB_NAME=norugs
   DB_USER=postgres
   DB_PASSWORD=your_postgresql_password

   # Optional live data providers — the app works without these,
   # but adding them raises rate limits and unlocks extra data.
   COINGECKO_API_KEY=
   COINGECKO_PLAN=demo
   ETHERSCAN_API_KEY=
   GITHUB_TOKEN=

   HTTP_TIMEOUT_SECONDS=30
   LOG_LEVEL=INFO

   # Background live-update engine
   LIVE_UPDATES_ENABLED=true
   LIVE_UPDATE_INTERVAL_SECONDS=60
   LIVE_UPDATE_ON_START=true
   ```

3. Save the file.

**Important:** double-check `DB_PORT` and `DB_USER` against what you actually set up in Step 2 — a standard PostgreSQL installer defaults to port `5432` and user `postgres`, but if you used Postgres.app on macOS it's commonly port `5433` and your Mac username instead. Getting this wrong is the most common reason the app can't connect.

### (Optional) Getting free API keys

The app runs and scores assets without any API keys, using public endpoints. Adding free keys raises rate limits and improves reliability:

- **CoinGecko** — https://www.coingecko.com/en/api/pricing → free Demo plan. Paste the key into `COINGECKO_API_KEY`.
- **Etherscan** — https://etherscan.io/apis → free account. Paste the key into `ETHERSCAN_API_KEY`.
- **GitHub** — https://github.com/settings/tokens → generate a personal access token (no special scopes needed for public repo data). Paste it into `GITHUB_TOKEN`.

---

## Step 11 — Start the application

With your virtual environment still active:

```bash
norugs-web
```

(or `python run.py` if you installed with `requirements.txt` in Step 7.)

You should see log output ending with something like `Running on http://127.0.0.1:5000`. Leave this terminal window open — closing it stops the server.

---

## Step 12 — Verify it's working

Open a web browser (Chrome or Edge recommended) and visit each of these in turn:

1. **`http://127.0.0.1:5000/`** — the NoRugs landing page should load.
2. **`http://127.0.0.1:5000/api/health`** — should show JSON containing `"status": "ok"` and confirmation the database is connected. If this shows an error instead, re-check your `.env` values from Step 10 and make sure PostgreSQL is running.
3. **`http://127.0.0.1:5000/dashboard.html`** — the live dashboard.

> Always use an `http://127.0.0.1:5000/...` address. Do not open the HTML files directly by double-clicking them from your file explorer (a `file:///...` address) — the page will load but won't be able to reach the API.

The first time the server starts, it automatically kicks off a background data-collection cycle (because `LIVE_UPDATE_ON_START=true`). Give it 30–60 seconds, then refresh the dashboard — the stat cards should populate with real tracked assets and risk scores.

If you'd rather trigger data collection manually instead of waiting, open a **second** terminal, activate the virtual environment again (Step 6), and run:

```bash
norugs-scrape --provider all
```

---

## Step 13 — Explore the app

With the server running, these pages are all available:

| Page | Address |
|---|---|
| Landing page | `http://127.0.0.1:5000/` |
| Dashboard | `http://127.0.0.1:5000/dashboard.html` |
| Coin Analysis | `http://127.0.0.1:5000/coin-analysis.html` |
| Portfolio Analysis | `http://127.0.0.1:5000/wallet-analysis.html` |
| Comparison | `http://127.0.0.1:5000/comparison.html` |
| Watchlist | `http://127.0.0.1:5000/watchlist.html` |
| Alerts | `http://127.0.0.1:5000/alerts.html` |

---

## Starting it again later

Once everything above is set up, restarting NoRugs on future days only takes two commands from inside the project folder:

**Windows**
```bat
.venv\Scripts\activate
norugs-web
```

**macOS**
```bash
source .venv/bin/activate
norugs-web
```

Then open `http://127.0.0.1:5000/dashboard.html`. Make sure PostgreSQL is running in the background first (pgAdmin, or Postgres.app on macOS).

---

## Troubleshooting

**`'py' is not recognized...` (Windows) or `command not found: python3` (macOS)**
Python wasn't installed correctly, or the installer needs a restart of your terminal window to be picked up. Close and reopen Command Prompt / Terminal and try again. On Windows, re-run the Python installer if `py --version` still fails. Note this only applies *before* Step 6 — after the virtual environment is created and activated, use plain `python` on both platforms, per the note in Step 6.

**`command not found: norugs-web`**
The virtual environment isn't active, or Step 7 didn't complete. Run:
```bash
source .venv/bin/activate   # or .venv\Scripts\activate on Windows
python -m pip install -e .
```

**`/api/health` shows a database error, or the dashboard is empty**
- Confirm PostgreSQL is actually running (check pgAdmin, or Postgres.app's menu bar icon on macOS).
- Re-check `DB_HOST`, `DB_PORT`, `DB_USER`, and `DB_PASSWORD` in `.env` against your actual PostgreSQL setup.
- Confirm the `norugs` database exists and that Step 9 (loading the schema) completed without errors.

**Dashboard loads but shows no assets / all zeros**
Data collection may not have run yet. Wait about a minute after starting the server, or trigger it manually with `norugs-scrape --provider all` (Step 12).

**`Port 5000 is already in use`**
Something else on your computer is using port 5000. Start on a different port instead:
```bash
PORT=5001 norugs-web        # macOS
set PORT=5001 && norugs-web # Windows (Command Prompt)
```
Then visit `http://127.0.0.1:5001/dashboard.html`.

**`psql: command not found` (Step 9, Option B)**
Use Option A (pgAdmin's Query Tool) instead — no command-line tool required.

---

## Project structure, for reference

```
NoRugs/
├── .env                    # your local configuration (created in Step 10, not shared/committed)
├── run.py                  # entry point: python run.py
├── pyproject.toml          # dependency list and CLI command definitions
├── config/assets.json      # which cryptocurrencies/repos to track
├── database/schema.sql     # full PostgreSQL schema (load this in Step 9)
├── frontend/               # dashboard, coin-analysis, comparison, watchlist, alerts, wallet-analysis pages
└── src/norugs_scraper/     # Flask app, data collector, and risk-scoring engine
```

You're done — NoRugs should now be running end to end on your machine.
