from __future__ import annotations

from uuid import UUID

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from backend.data_pipeline.silver.schemas.submarkets import SubmarketRecord


class VacancyCompressionCalculator:
    """Measures how tight a submarket is relative to the borough-wide average.

    Positive values indicate the submarket is tighter (lower vacancy) than
    the borough average; negative values indicate looser conditions.
    """

    async def compute(self, session: AsyncSession, submarket_id: UUID) -> float | None:
        submarket_vacancy_statement = (
            select(SubmarketRecord.vacancy_rate)
            .where(SubmarketRecord.submarket_id == submarket_id)
        )
        submarket_result = await session.execute(submarket_vacancy_statement)
        submarket_vacancy_rate = submarket_result.scalar_one_or_none()
        if submarket_vacancy_rate is None:
            return None

        borough_average_statement = (
            select(func.avg(SubmarketRecord.vacancy_rate))
            .where(SubmarketRecord.vacancy_rate.is_not(None))
        )
        borough_result = await session.execute(borough_average_statement)
        borough_average_vacancy = borough_result.scalar_one_or_none()
        if not borough_average_vacancy:
            return None

        borough_average = float(borough_average_vacancy)
        submarket_rate = float(submarket_vacancy_rate)

        return round((borough_average - submarket_rate) / borough_average, 4)
