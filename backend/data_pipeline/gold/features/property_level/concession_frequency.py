from __future__ import annotations

from datetime import date, timedelta
from uuid import UUID

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from backend.data_pipeline.silver.schemas.building_violations import BuildingViolationRecord
from backend.data_pipeline.silver.schemas.properties import PropertyRecord
from backend.data_pipeline.silver.schemas.submarkets import SubmarketRecord

_TRAILING_WINDOW_DAYS = 365


class PermitActivityScoreCalculator:
    """Scores development/renovation pressure near a property using DOB
    violation filings as a proxy for permit activity, combined with the
    submarket's supply pipeline.

    Returns ratio of local activity to borough-wide average, normalized
    to 0.0–1.0 (1.0 = heavy activity, 0.0 = none).
    """

    async def compute(self, session: AsyncSession, property_id: UUID) -> float | None:
        property_statement = (
            select(PropertyRecord.submarket_id)
            .where(PropertyRecord.property_id == property_id)
        )
        property_result = await session.execute(property_statement)
        submarket_id = property_result.scalar_one_or_none()
        if submarket_id is None:
            return None

        zip_code_statement = (
            select(SubmarketRecord.zip_code, SubmarketRecord.supply_pipeline_units)
            .where(SubmarketRecord.submarket_id == submarket_id)
        )
        zip_result = await session.execute(zip_code_statement)
        zip_row = zip_result.one_or_none()
        if zip_row is None:
            return None

        local_zip_code, supply_pipeline_units = zip_row

        cutoff_date = date.today() - timedelta(days=_TRAILING_WINDOW_DAYS)

        local_violations_statement = (
            select(func.count())
            .select_from(BuildingViolationRecord)
            .where(
                BuildingViolationRecord.source == "DOB",
                BuildingViolationRecord.violation_date >= cutoff_date,
                BuildingViolationRecord.property_id.in_(
                    select(PropertyRecord.property_id).where(
                        PropertyRecord.submarket_id == submarket_id
                    )
                ),
            )
        )
        local_result = await session.execute(local_violations_statement)
        local_violation_count = local_result.scalar_one() or 0

        borough_wide_violations_statement = (
            select(func.count())
            .select_from(BuildingViolationRecord)
            .where(
                BuildingViolationRecord.source == "DOB",
                BuildingViolationRecord.violation_date >= cutoff_date,
            )
        )
        borough_result = await session.execute(borough_wide_violations_statement)
        borough_violation_count = borough_result.scalar_one() or 0

        total_submarkets_statement = (
            select(func.count()).select_from(SubmarketRecord)
        )
        total_submarkets_result = await session.execute(total_submarkets_statement)
        total_submarket_count = total_submarkets_result.scalar_one() or 1

        borough_average = borough_violation_count / total_submarket_count

        pipeline_signal = float(supply_pipeline_units) if supply_pipeline_units else 0.0

        combined_local_activity = local_violation_count + (pipeline_signal * 0.1)
        combined_borough_average = borough_average + (pipeline_signal * 0.05)

        if combined_borough_average == 0:
            return 0.0

        ratio = combined_local_activity / combined_borough_average
        score = min(ratio / 2.0, 1.0)
        return round(score, 4)
