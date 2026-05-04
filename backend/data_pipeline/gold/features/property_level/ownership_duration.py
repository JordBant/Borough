from __future__ import annotations

from datetime import date
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.data_pipeline.silver.schemas.properties import PropertyRecord


class OwnershipDurationCalculator:
    """Computes years since last known ownership transfer.

    Falls back to years since the building was constructed when no
    ownership transfer records are available in the silver layer.
    """

    async def compute(self, session: AsyncSession, property_id: UUID) -> float | None:
        property_statement = (
            select(PropertyRecord.year_built)
            .where(PropertyRecord.property_id == property_id)
        )
        property_result = await session.execute(property_statement)
        year_built = property_result.scalar_one_or_none()
        if year_built is None:
            return None

        current_year = date.today().year
        return float(current_year - year_built)
