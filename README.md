# NoRugs Installation Guide

This guide assumes you are starting with a brand-new computer.

---

## Step 1 - Install Python

Download Python 3.12 or newer from:

https://python.org

During installation check:

✔ Add Python to PATH

After installation verify it by opening Command Prompt (Windows) or Terminal (macOS) and typing:

python --version

---

## Step 2 - Install PostgreSQL

Download PostgreSQL from:

https://www.postgresql.org/download/

During installation:

• Leave the port as 5432

• Remember the password you create

Open pgAdmin after installation and make sure the PostgreSQL server is running.

---

## Step 3 - Download NoRugs

Clone the repository:

git clone https://github.com/USERNAME/NoRugs.git

or download the ZIP from GitHub and extract it.

---

## Step 4 - Open the project

Open the NoRugs folder in Visual Studio Code.

Open a terminal.

---

## Step 5 - Install the required packages

Run:

pip install -r requirements.txt

Wait until installation finishes.

---

## Step 6 - Create the database

Open pgAdmin.

Create a new database named:

norugs

---

## Step 7 - Import the database

Open Query Tool.

Open:

database/schema.sql

Execute the script.

---

## Step 8 - Configure the application

Locate the database configuration file inside the config folder.

Replace the default values with your PostgreSQL information.

Example:

Database name:
norugs

Username:
postgres

Password:
YOUR_PASSWORD

Host:
localhost

Port:
5432

Save the file.

---

## Step 9 - Start NoRugs

Run:

python run.py

---

## Step 10 - Open the website

Open your browser.

Navigate to:

http://localhost:5000

You should now see the NoRugs dashboard.

---

## Troubleshooting

Python not found

Install Python and make sure "Add Python to PATH" was selected.

Database connection failed

Verify PostgreSQL is running and the username, password, and database name are correct.

Missing package

Run:

pip install -r requirements.txt

Port already in use

Close the other application using that port or update the application's configuration.

---

Congratulations!

NoRugs is now installed and ready to use.