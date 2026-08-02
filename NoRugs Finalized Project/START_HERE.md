# Start NoRugs on macOS

## Before you begin

Install these applications if they are not already installed:

1. Python 3.11 or newer
2. PostgreSQL and pgAdmin 4
3. Visual Studio Code (optional, but recommended)

## Step 1 — Extract and open the project

1. Double-click the downloaded ZIP file.
2. Move the `NoRugs_Integrated` folder somewhere easy to find, such as Documents.
3. Open Visual Studio Code.
4. Select **File → Open Folder** and choose `NoRugs_Integrated`.
5. In VS Code, select **Terminal → New Terminal**.

Every command below should be run from the `NoRugs_Integrated` folder.

## Step 2 — Create the PostgreSQL database

Open pgAdmin and create a database named `norugs`.

Then load `database/schema.sql` using either pgAdmin's Query Tool or Terminal:

```bash
psql -U postgres -d norugs -f database/schema.sql
```

Replace `postgres` with your PostgreSQL username when necessary.

## Step 3 — Create the Python environment

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
pip install -e .
```

When the environment is active, the Terminal prompt begins with `(.venv)`.

## Step 4 — Configure the database connection

Create your working environment file:

```bash
cp .env.example .env
```

Open `.env` in VS Code and enter the values used by your PostgreSQL installation:

```env
DB_HOST=localhost
DB_PORT=5432
DB_NAME=norugs
DB_USER=postgres
DB_PASSWORD=your_postgresql_password
```

Most PostgreSQL installations use port `5432`. Use `5433` only when pgAdmin shows that your server is using that port.

## Step 5 — Test the website

Start the Flask server:

```bash
norugs-web
```

Open this address in Chrome:

```text
http://127.0.0.1:5000/dashboard.html
```

Do not open the HTML pages by double-clicking them. A `file:///...` address cannot use the Flask API correctly. The browser address must begin with `http://127.0.0.1:5000`.

## Step 6 — Check the database connection

Open:

```text
http://127.0.0.1:5000/api/health
```

A working connection displays a JSON response containing `"status": "ok"` and `"database": "connected"`.

## Step 7 — Collect market data

Stop the server with **Control+C**, or open a second Terminal and activate the environment again:

```bash
source .venv/bin/activate
```

Run the collectors:

```bash
norugs-scrape --provider coingecko
norugs-scrape --provider dexscreener
norugs-scrape --provider github
norugs-scrape --provider risk
```

To run all configured providers in sequence:

```bash
norugs-scrape --provider all
```

Then restart the website:

```bash
norugs-web
```

## Starting it again later

```bash
cd /path/to/NoRugs_Integrated
source .venv/bin/activate
norugs-web
```

Then open `http://127.0.0.1:5000/dashboard.html`.

## Common problems

### `command not found: norugs-web`

Activate the virtual environment and reinstall the project:

```bash
source .venv/bin/activate
pip install -e .
```

### Database unavailable

Check that PostgreSQL is running and verify `DB_PORT`, `DB_USER`, and `DB_PASSWORD` in `.env`.

### The page opens but only shows demo data

Confirm that you opened the HTTP address instead of the local HTML file, test `/api/health`, and run the data collectors.

### Port 5000 is already in use

```bash
PORT=5001 norugs-web
```

Then open `http://127.0.0.1:5001/dashboard.html`.
