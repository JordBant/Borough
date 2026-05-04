from __future__ import annotations

from datetime import date, timedelta
from uuid import UUID

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from backend.data_pipeline.silver.schemas.neighborhood_signals import NeighborhoodSignalRecord

_TRAILING_WINDOW_DAYS = 180
_MAX_COMPLAINT_DENSITY = 500.0


class NeighborhoodComplaintDensityCalculator:
    """Counts housing-related 311 complaints for the submarket in the
    trailing 6 months.

    Higher complaint density signals worse neighborhood quality.
    Returns a normalized score 0.0–1.0 (1.0 = highest complaint density).
    """

    async def compute(self, session: AsyncSession, submarket_id: UUID) -> float | None:
        cutoff_date = date.today() - timedelta(days=_TRAILING_WINDOW_DAYS)

        local_complaint_statement = (
            select(func.coalesce(func.sum(NeighborhoodSignalRecord.complaint_count), 0))
            .where(
                NeighborhoodSignalRecord.submarket_id == submarket_id,
                NeighborhoodSignalRecord.period_start >= cutoff_date,
            )
        )
        local_result = await session.execute(local_complaint_statement)
        local_complaint_total = local_result.scalar_one() or 0

        if local_complaint_total == 0:
            return 0.0

        all_complaints_statement = (
            select(func.coalesce(func.sum(NeighborhoodSignalRecord.complaint_count), 0))
            .where(NeighborhoodSignalRecord.period_start >= cutoff_date)
        )
        all_result = await session.execute(all_complaints_statement)
        total_complaint_count = all_result.scalar_one() or 0

        submarket_count_statement = (
            select(func.count(func.distinct(NeighborhoodSignalRecord.submarket_id)))
            .where(NeighborhoodSignalRecord.period_start >= cutoff_date)
        )
        submarket_count_result = await session.execute(submarket_count_statement)
        active_submarket_count = submarket_count_result.scalar_one() or 1

        average_complaints_per_submarket = total_complaint_count / active_submarket_count

        if average_complaints_per_submarket == 0:
            return 0.0

        ratio = local_complaint_total / average_complaints_per_submarket
        score = min(ratio / 2.0, 1.0)
        return round(score, 4)
