from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from psycopg2.extras import RealDictCursor

from api.routes.coins import router as coins_router
from api.routes.stats import router as stats_router
from api.schemas import HealthResponse
from database.connection import get_database_connection


app = FastAPI(
    title="NoRugs API",
    version="1.0.0",
    description=(
        "Cryptocurrency market monitoring and "
        "transparent risk-assessment API."
    ),
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "http://localhost:5500",
        "http://127.0.0.1:5500",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(coins_router)
app.include_router(stats_router)


@app.get("/", tags=["system"])
def root() -> dict[str, str]:
    return {
        "name": "NoRugs API",
        "version": "1.0.0",
        "documentation": "/docs",
    }


@app.get(
    "/api/health",
    response_model=HealthResponse,
    tags=["system"],
)
def health_check() -> dict[str, str]:
    query = "SELECT current_database() AS database;"

    with get_database_connection() as connection:
        with connection.cursor(
            cursor_factory=RealDictCursor
        ) as cursor:
            cursor.execute(query)
            result = cursor.fetchone()

    return {
        "status": "healthy",
        "database": result["database"],
    }