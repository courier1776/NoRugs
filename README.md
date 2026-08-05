# NoRugs Setup Guide

Follow these instructions from top to bottom on a brand-new Windows or macOS computer. No coding experience is required.

When finished, NoRugs will run at:

```text
http://127.0.0.1:5000/dashboard.html
```

> **Important:** Complete the steps for your operating system only.

---

# 1. Install Python

NoRugs requires Python 3.11 or 3.12.

## Windows

1. Open a web browser.
2. Go to: <https://www.python.org/downloads/>
3. Click the yellow **Download Python 3** button.
4. Open the downloaded installer from the browser's Downloads list.
5. On the first installer screen, check **Add python.exe to PATH**.
6. Click **Install Now**.
7. If Windows asks whether the installer can make changes, click **Yes**.
8. Wait for the installation to finish.
9. Click **Close**.

Do not continue until Python works:

1. Open the Windows **Start** menu.
2. Type `PowerShell`.
3. Open **Windows PowerShell**.
4. Enter:

```powershell
py --version
```

You should see Python 3.11 or 3.12.

If the command is not recognized, restart the computer and try again. If it still fails, run the Python installer again and confirm **Add python.exe to PATH** is checked.

## macOS

1. Open a web browser.
2. Go to: <https://www.python.org/downloads/>
3. Click the yellow **Download Python 3** button.
4. Open the downloaded `.pkg` file.
5. Click **Continue**.
6. Click **Continue** again.
7. Click **Agree**.
8. Click **Install**.
9. Enter the Mac password if asked.
10. Click **Close** when installation finishes.

Do not continue until Python works:

1. Open **Finder**.
2. Click **Applications**.
3. Open **Utilities**.
4. Open **Terminal**.
5. Enter:

```bash
python3 --version
```

You should see Python 3.11 or 3.12.

---

# 2. Install PostgreSQL and pgAdmin 4

Use the EnterpriseDB installer on both Windows and macOS. Do not use Postgres.app for this setup.

## Windows

1. Open a web browser.
2. Go to: <https://www.postgresql.org/download/windows/>
3. Click **Download the installer**.
4. The EnterpriseDB download page will open.
5. Find the newest PostgreSQL version available for **Windows x86-64**.
6. Click the download icon in that row.
7. Open the downloaded installer.
8. If Windows asks whether the installer can make changes, click **Yes**.
9. Click **Next**.
10. Leave the installation folder unchanged and click **Next**.
11. Leave these components selected:
    - PostgreSQL Server
    - pgAdmin 4
    - Stack Builder
    - Command Line Tools
12. Click **Next**.
13. Leave the data folder unchanged and click **Next**.
14. Create a password for the `postgres` account.
15. Write the password down. You will need it later.
16. Click **Next**.
17. Leave the port set to `5432`.
18. Click **Next**.
19. Leave the locale at its default value.
20. Click **Next**.
21. Click **Next** again.
22. Click **Finish** when installation completes.
23. If Stack Builder opens, close it. No additional packages are required.

## macOS

1. Open a web browser.
2. Go to: <https://www.postgresql.org/download/macosx/>
3. Under **Interactive installer by EDB**, click **Download the installer**.
4. The EnterpriseDB download page will open.
5. Find the newest PostgreSQL version available for **macOS**.
6. Click the download icon in that row.
7. Open the downloaded installer.
8. If macOS displays a security prompt, click **Open**.
9. Click **Next**.
10. Leave the installation folder unchanged and click **Next**.
11. Leave these components selected:
    - PostgreSQL Server
    - pgAdmin 4
    - Stack Builder
    - Command Line Tools
12. Click **Next**.
13. Leave the data folder unchanged and click **Next**.
14. Create a password for the `postgres` account.
15. Write the password down. You will need it later.
16. Click **Next**.
17. Leave the port set to `5432`.
18. Click **Next**.
19. Leave the locale at its default value.
20. Click **Next**.
21. Click **Next** again.
22. Enter the Mac password if asked.
23. Click **Finish** when installation completes.
24. If Stack Builder opens, close it. No additional packages are required.

## Confirm PostgreSQL is working

1. Open **pgAdmin 4**.
   - Windows: Open the Start menu, type `pgAdmin 4`, and click it.
   - macOS: Open Applications and double-click **pgAdmin 4**.
2. The first time pgAdmin opens, it may ask for a master password. Create one and remember it.
3. In the left panel, click the arrow beside **Servers**.
4. Click the arrow beside the PostgreSQL server.
5. Enter the PostgreSQL password created during installation.
6. Click **OK**.

If the server opens without an error, PostgreSQL is running.

---

# 3. Install Visual Studio Code

## Windows

1. Open a web browser.
2. Go to: <https://code.visualstudio.com/>
3. Click **Download for Windows**.
4. Open the downloaded installer.
5. Accept the license agreement.
6. Click **Next**.
7. Leave the installation folder unchanged and click **Next**.
8. Leave the Start Menu folder unchanged and click **Next**.
9. On **Select Additional Tasks**, check:
    - Add "Open with Code" action to Windows Explorer file context menu
    - Add "Open with Code" action to Windows Explorer directory context menu
    - Register Code as an editor for supported file types
    - Add to PATH
10. Click **Next**.
11. Click **Install**.
12. Leave **Launch Visual Studio Code** checked.
13. Click **Finish**.

## macOS

1. Open a web browser.
2. Go to: <https://code.visualstudio.com/>
3. Click **Download Mac Universal**.
4. Open the downloaded ZIP file.
5. Drag **Visual Studio Code** into the **Applications** folder.
6. Open **Applications**.
7. Double-click **Visual Studio Code**.
8. If macOS asks whether to open the downloaded application, click **Open**.

No VS Code extensions are required to run NoRugs.

---

# 4. Download the NoRugs project

Use the ZIP method. Git is not required to run the application.

1. Open the NoRugs GitHub repository in a web browser:

```text
https://github.com/YOUR-GITHUB-USERNAME/NoRugs
```

2. Replace `YOUR-GITHUB-USERNAME` with the GitHub username that owns the NoRugs repository.
3. Click the green **Code** button.
4. Click **Download ZIP**.
5. Wait for the download to finish.

## Windows

1. Open **File Explorer**.
2. Click **Downloads**.
3. Right-click the NoRugs ZIP file.
4. Click **Extract All**.
5. Click **Browse**.
6. Select **Desktop**.
7. Click **Select Folder**.
8. Click **Extract**.
9. Rename the extracted folder to `NoRugs` if it has a different name such as `NoRugs-main`.

## macOS

1. Open **Finder**.
2. Click **Downloads**.
3. Double-click the NoRugs ZIP file.
4. Drag the extracted folder to the Desktop.
5. Rename the folder to `NoRugs` if it has a different name such as `NoRugs-main`.

---

# 5. Open NoRugs in VS Code

1. Open Visual Studio Code.
2. Click **File** in the top menu.
3. Click **Open Folder**.
4. Click **Desktop**.
5. Select the `NoRugs` folder.
6. Click **Select Folder** on Windows or **Open** on macOS.
7. If VS Code asks whether you trust the authors, click **Yes, I trust the authors**.
8. Click **Terminal** in the top menu.
9. Click **New Terminal**.

The terminal should open at the bottom of VS Code. The terminal path should end in `NoRugs`.

---

# 6. Create the Python virtual environment

## Windows PowerShell

Enter these commands one at a time in the VS Code terminal:

```powershell
py -m venv .venv
```

```powershell
.venv\Scripts\Activate.ps1
```

If PowerShell says script execution is disabled, enter:

```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
```

Then enter the activation command again:

```powershell
.venv\Scripts\Activate.ps1
```

## macOS

Enter these commands one at a time in the VS Code terminal:

```bash
python3 -m venv .venv
```

```bash
source .venv/bin/activate
```

After activation, the terminal line should begin with:

```text
(.venv)
```

Do not continue until `(.venv)` appears.

---

# 7. Install the NoRugs dependencies

Make sure `(.venv)` appears in the terminal. Then enter these commands one at a time:

```bash
python -m pip install --upgrade pip
```

```bash
python -m pip install -e .
```

Wait for the installation to finish.

If the second command fails, enter:

```bash
python -m pip install -r requirements.txt
```

---

# 8. Create the NoRugs database

1. Open **pgAdmin 4**.
2. In the left panel, expand **Servers**.
3. Expand the PostgreSQL server.
4. Enter the PostgreSQL password if asked.
5. Right-click **Databases**.
6. Click **Create**.
7. Click **Database**.
8. In the **Database** box, enter:

```text
norugs
```

9. Leave the Owner set to `postgres`.
10. Click **Save**.

The `norugs` database should now appear under Databases.

---

# 9. Load the database schema

1. In pgAdmin, right-click the new `norugs` database.
2. Click **Query Tool**.
3. Click the folder icon near the top of the Query Tool.
4. Browse to the `NoRugs` folder on the Desktop.
5. Open the `database` folder.
6. Select `schema.sql`.
7. Click **Open**.
8. Click the Execute button shaped like a triangle, or press **F5**.
9. Wait for the query to finish.

The Messages panel should show that the query completed successfully. Do not continue if pgAdmin displays a red error.

---

# 10. Create the `.env` configuration file

1. Return to Visual Studio Code.
2. In the Explorer panel on the left, right-click the top `NoRugs` folder.
3. Click **New File**.
4. Enter this exact file name:

```text
.env
```

5. Press Enter.
6. Paste the following text into the file:

```env
DB_HOST=localhost
DB_PORT=5432
DB_NAME=norugs
DB_USER=postgres
DB_PASSWORD=REPLACE_WITH_YOUR_POSTGRES_PASSWORD

COINGECKO_API_KEY=
COINGECKO_PLAN=demo
ETHERSCAN_API_KEY=
GITHUB_TOKEN=

HTTP_TIMEOUT_SECONDS=30
LOG_LEVEL=INFO

LIVE_UPDATES_ENABLED=true
LIVE_UPDATE_INTERVAL_SECONDS=60
LIVE_UPDATE_ON_START=true
```

7. Replace `REPLACE_WITH_YOUR_POSTGRES_PASSWORD` with the password created during PostgreSQL installation.
8. Do not add quotation marks around the password.
9. Save the file:
   - Windows: press **Ctrl + S**.
   - macOS: press **Command + S**.

The API-key fields can remain blank for the initial setup. Public data providers may apply rate limits, and providers that require authentication may return limited or no data until a key is added.

> Never upload the `.env` file to GitHub. It can contain passwords and API keys.

---

# 11. Start NoRugs

Return to the VS Code terminal. Make sure `(.venv)` still appears.

Enter:

```bash
norugs-web
```

If `norugs-web` is not recognized, enter:

```bash
python run.py
```

Leave the terminal open. Closing it stops NoRugs.

Wait until the terminal shows an address similar to:

```text
Running on http://127.0.0.1:5000
```

---

# 12. Open NoRugs in a browser

Open a web browser and visit:

```text
http://127.0.0.1:5000/dashboard.html
```

Do not open the HTML files by double-clicking them. Always use the `http://127.0.0.1:5000` address.

The first live-data update can take 30 to 60 seconds. Refresh the dashboard after one minute.

---

# 13. Check that the database connection works

Open this address:

```text
http://127.0.0.1:5000/api/health
```

The page should show JSON containing:

```json
"status": "ok"
```

If it reports a database error, check these items:

1. PostgreSQL is running.
2. The `norugs` database exists.
3. `database/schema.sql` completed without an error.
4. The password in `.env` matches the PostgreSQL password.
5. `DB_PORT` is `5432`.
6. `DB_USER` is `postgres`.

---

# 14. Run a manual data update

The server performs background updates automatically. To run one manually:

1. In VS Code, click **Terminal**.
2. Click **New Terminal**.
3. Activate the virtual environment.

Windows PowerShell:

```powershell
.venv\Scripts\Activate.ps1
```

macOS:

```bash
source .venv/bin/activate
```

4. Run:

```bash
norugs-scrape --provider all
```

If that command is unavailable, keep the main server running and wait for the automatic update.

---

# 15. Start NoRugs again later

PostgreSQL must be running before NoRugs starts.

## Windows

1. Open VS Code.
2. Click **File** → **Open Folder**.
3. Select the `NoRugs` folder.
4. Click **Terminal** → **New Terminal**.
5. Enter:

```powershell
.venv\Scripts\Activate.ps1
```

6. Enter:

```powershell
norugs-web
```

If that command is unavailable, enter:

```powershell
python run.py
```

## macOS

1. Open VS Code.
2. Click **File** → **Open Folder**.
3. Select the `NoRugs` folder.
4. Click **Terminal** → **New Terminal**.
5. Enter:

```bash
source .venv/bin/activate
```

6. Enter:

```bash
norugs-web
```

If that command is unavailable, enter:

```bash
python run.py
```

Then open:

```text
http://127.0.0.1:5000/dashboard.html
```

---

# Troubleshooting

## PowerShell says scripts are disabled

Run:

```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
```

Then activate the environment again:

```powershell
.venv\Scripts\Activate.ps1
```

## `norugs-web` is not recognized

Make sure the virtual environment is active, then run:

```bash
python -m pip install -e .
```

If it still does not work, start the application with:

```bash
python run.py
```

## The dashboard loads but contains no data

1. Wait 60 seconds.
2. Refresh the page.
3. Confirm the terminal remains open.
4. Check `http://127.0.0.1:5000/api/health`.
5. Run the manual update from Step 14.

## Port 5000 is already in use

### Windows PowerShell

```powershell
$env:PORT=5001
norugs-web
```

If needed:

```powershell
$env:PORT=5001
python run.py
```

### macOS

```bash
PORT=5001 norugs-web
```

If needed:

```bash
PORT=5001 python run.py
```

Then open:

```text
http://127.0.0.1:5001/dashboard.html
```

## The database password does not work

The password in `.env` must be the PostgreSQL password created during installation. It is not the computer login password and not the pgAdmin master password.

---

# Project structure

```text
NoRugs/
├── .env
├── run.py
├── pyproject.toml
├── requirements.txt
├── config/
│   └── assets.json
├── database/
│   └── schema.sql
├── frontend/
└── src/
    └── norugs_scraper/
```

NoRugs is now installed and running.
