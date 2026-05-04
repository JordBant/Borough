from __future__ import annotations

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.data_pipeline.silver.schemas.leases import LeaseRecord
from backend.data_pipeline.silver.schemas.properties import PropertyRecord


class RentPerSquareFootCalculator:

    async def compute(self, session: AsyncSession, property_id: UUID) -> float | None:
        latest_lease_statement = (
            select(LeaseRecord.signed_rent)
            .where(LeaseRecord.property_id == property_id)
            .order_by(LeaseRecord.lease_start_date.desc())
            .limit(1)
        )
        lease_result = await session.execute(latest_lease_statement)
        signed_rent = lease_result.scalar_one_or_none()
        if signed_rent is None:
            return None

        property_statement = (
            select(PropertyRecord.square_footage)
            .where(PropertyRecord.property_id == property_id)
        )
        property_result = await session.execute(property_statement)
        square_footage = property_result.scalar_one_or_none()
        if not square_footage:
            return None

        return float(signed_rent) / float(square_footage)
