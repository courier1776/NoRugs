import json

from database.connection import get_database_connection
from risk_engine.scorer import RiskResult


class RiskRepository:
    def get_active_model_id(self) -> int:
        query = """
        SELECT risk_model_id
        FROM risk_models
        WHERE model_name = 'NoRugs Core Risk Model'
          AND is_active = TRUE
        ORDER BY created_at DESC
        LIMIT 1;
        """

        with get_database_connection() as connection:
            with connection.cursor() as cursor:
                cursor.execute(query)
                result = cursor.fetchone()

                if result is None:
                    raise RuntimeError("No active risk model was found.")

                return result[0]

    def save_assessment(
        self,
        cryptocurrency_id: int,
        result: RiskResult,
    ) -> int:
        assessment_query = """
        INSERT INTO risk_assessments (
            cryptocurrency_id,
            risk_model_id,
            overall_risk_score,
            risk_level,
            confidence_score,
            summary
        )
        VALUES (%s, %s, %s, %s, %s, %s)
        RETURNING risk_assessment_id;
        """

        factor_query = """
        INSERT INTO risk_factor_scores (
            risk_assessment_id,
            factor_name,
            factor_score,
            weight,
            weighted_score,
            explanation,
            evidence
        )
        VALUES (%s, %s, %s, %s, %s, %s, %s);
        """

        with get_database_connection() as connection:
            with connection.cursor() as cursor:
                cursor.execute(
                    assessment_query,
                    (
                        cryptocurrency_id,
                        self.get_active_model_id(),
                        result.overall_score,
                        result.risk_level,
                        result.confidence_score,
                        result.summary,
                    ),
                )

                assessment = cursor.fetchone()

                if assessment is None:
                    raise RuntimeError(
                        "Risk assessment ID was not returned."
                    )

                assessment_id = assessment[0]

                for factor in result.factors:
                    cursor.execute(
                        factor_query,
                        (
                            assessment_id,
                            factor["name"],
                            factor["score"],
                            factor["weight"],
                            factor["score"] * factor["weight"],
                            factor["explanation"],
                            json.dumps(factor["evidence"]),
                        ),
                    )

                return assessment_id