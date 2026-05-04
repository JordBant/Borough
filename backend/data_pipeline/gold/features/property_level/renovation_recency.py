from __future__ import annotations

from datetime import date, timedelta
from uuid import UUID

from sqlalchemy import select, func, case
from sqlalchemy.ext.asyncio import AsyncSession

from backend.data_pipeline.silver.schemas.building_violations import BuildingViolationRecord

_TRAILING_WINDOW_DAYS = 730  # 24 months

_VIOLATION_WEIGHTS = {
    "C": 3.0,
    "B": 2.0,
    "A": 1.0,
}
_DOB_WEIGHT = 1.5

_MAX_WEIGHTED_VIOLATIONS = 30.0


class BuildingQualityScoreCalculator:
    """Scores building quality from DOB + HPD violations in the trailing
    24 months.

    Weights: HPD class C (immediately hazardous) = 3x, class B = 2x,
    class A = 1x, DOB violations = 1.5x.

    Returns 0.0–1.0 where 1.0 = excellent quality (no violations).
    """

    async def compute(self, session: AsyncSession, property_id: UUID) -> float | None:
        cutoff_date = date.today() - timedelta(days=_TRAILING_WINDOW_DAYS)

        violations_statement = (
            select(
                BuildingViolationRecord.source,
                BuildingViolationRecord.violation_class,
            )
            .where(
                BuildingViolationRecord.property_id == property_id,
                BuildingViolationRecord.violation_date >= cutoff_date,
            )
        )
        violations_result = await session.execute(violations_statement)
        violation_rows = violations_result.all()

        if not violation_rows:
            return 1.0

        weighted_total = 0.0
        for source, violation_class in violation_rows:
            if source and source.upper() == "DOB":
                weighted_total += _DOB_WEIGHT
            else:
                weight = _VIOLATION_WEIGHTS.get(
                    violation_class.upper() if violation_class else "", 1.0
                )
                weighted_total += weight

        score = max(0.0, 1.0 - (weighted_total / _MAX_WEIGHTED_VIOLATIONS))
        return round(score, 4)
