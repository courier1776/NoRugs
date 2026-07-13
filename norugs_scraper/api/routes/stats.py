from fastapi import APIRouter
from psycopg2.extras import RealDictCursor

from api.schemas import DashboardStats
from database.connection import get_database_connection


router = APIRouter(
    prefix="/api/stats",
    tags=["statistics"],
)


@router.get("/dashboard", response_model=DashboardStats)
def get_dashboard_stats() -> dict:
    query = """
        SELECT
            COUNT(*) AS total_coins,
            COUNT(*) FILTER (
                WHERE risk_level = 'LOW'
            ) AS low_risk,
            COUNT(*) FILTER (
                WHERE risk_level = 'MODERATE'
            ) AS moderate_risk,
            COUNT(*) FILTER (
                WHERE risk_level = 'HIGH'
            ) AS high_risk,
            COUNT(*) FILTER (
                WHERE risk_level = 'CRITICAL'
            ) AS critical_risk,
            ROUND(AVG(overall_risk_score), 2)
                AS average_risk_score
        FROM cryptocurrency_dashboard;
    """

    with get_database_connection() as connection:
        with connection.cursor(
            cursor_factory=RealDictCursor
        ) as cursor:
            cursor.execute(query)
            return cursor.fetchone()