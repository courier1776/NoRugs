# NoRugs

## Overview

**NoRugs** is a cryptocurrency risk monitoring platform designed to help users evaluate the legitimacy and overall risk of cryptocurrency projects. The application combines market data, blockchain analysis, and historical indicators to generate an easy-to-understand risk assessment for each supported cryptocurrency.

The project is built using Python, PostgreSQL, and a web-based dashboard, making it suitable for research, education, and cryptocurrency risk analysis.

---

# Features

- Cryptocurrency risk scoring
- PostgreSQL database integration
- Cryptocurrency data collection
- Historical data storage
- Interactive web interface
- Modular architecture for future expansion

---

# System Requirements

Before installing NoRugs, install the following software:

- Python 3.12 or later
- PostgreSQL 17 or later
- Git
- Visual Studio Code (recommended)

---

# Installation

## 1. Clone or Download

Clone the repository:

```bash
git clone <repository-url>
```

or download the ZIP from GitHub and extract it.

Open the project folder in Visual Studio Code.

---

## 2. Create a Virtual Environment

### Windows

```bash
py -m venv .venv
.venv\Scripts\activate
```

### macOS

```bash
python3 -m venv .venv
source .venv/bin/activate
```

---

## 3. Upgrade pip

```bash
python -m pip install --upgrade pip
```

---

## 4. Install Project Dependencies

```bash
python -m pip install -r requirements.txt
```

---

## 5. Install the Project

```bash
python -m pip install -e .
```

---

# PostgreSQL Setup

1. Install PostgreSQL.
2. Use the default port:

```
5432
```

3. Create a database named:

```
norugs
```

4. Update your project configuration with your PostgreSQL credentials if required.

---

# Running the Application

Start the application:

```bash
python run.py
```

If successful, open your browser and navigate to:

```
http://127.0.0.1:5000
```

---

# Troubleshooting

## ModuleNotFoundError

Run:

```bash
python -m pip install -e .
```

## Missing Dependencies

Run:

```bash
python -m pip install -r requirements.txt
```

## PostgreSQL Connection Issues

- Verify PostgreSQL is running.
- Verify the database exists.
- Verify your credentials are correct.
- Verify PostgreSQL is listening on port **5432**.

---

# Project Structure

```
NoRugs/
│
├── src/
│   └── norugs_scraper/
├── run.py
├── requirements.txt
├── pyproject.toml
└── README.md
```

---

# Technologies

- Python
- PostgreSQL
- Flask
- SQLAlchemy
- HTML
- CSS
- JavaScript

---

# Future Enhancements

- Additional blockchain support
- Expanded risk indicators
- Real-time monitoring
- Enhanced dashboard analytics
- Automated alerts

---

# Disclaimer

NoRugs is intended for educational and research purposes. Risk scores are informational only and should not be considered financial advice.
