from __future__ import annotations

from datetime import date, timedelta
from uuid import UUID

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from backend.data_pipeline.silver.schemas.leases import LeaseRecord
from backend.data_pipeline.silver.schemas.properties import PropertyRecord
from backend.data_pipeline.silver.schemas.submarkets import SubmarketRecord


_ABSORPTION_LOOKBACK_DAYS = 365


class SupplyConstraintScoreCalculator:
    """Compares permitted new supply to the absorption rate.

    Low permitted units relative to high absorption → high constraint (1.0).
    High permitted units relative to low absorption → low constraint (0.0).
    Uses supply_pipeline_units from the submarket record as the supply proxy
    and trailing 12-month new lease volume as the absorption proxy.
    """

    async def compute(self, session: AsyncSession, submarket_id: UUID) -> float | None:
        supply_statement = (
            select(SubmarketRecord.supply_pipeline_units)
            .where(SubmarketRecord.submarket_id == submarket_id)
        )
        supply_result = await session.execute(supply_statement)
        supply_pipeline_units = supply_result.scalar_one_or_none()
        if supply_pipeline_units is None:
            return None

        submarket_property_ids = (
            select(PropertyRecord.property_id)
            .where(PropertyRecord.submarket_id == submarket_id)
        )

        cutoff_date = date.today() - timedelta(days=_ABSORPTION_LOOKBACK_DAYS)

        absorption_statement = (
            select(func.count())
            .select_from(LeaseRecord)
            .where(
                LeaseRecord.property_id.in_(submarket_property_ids),
                LeaseRecord.lease_start_date >= cutoff_date,
            )
        )
        absorption_result = await session.execute(absorption_statement)
        absorbed_lease_count = absorption_result.scalar_one()

        if absorbed_lease_count == 0 and supply_pipeline_units == 0:
            return 0.5

        supply_to_absorption_ratio = (
            float(supply_pipeline_units) / max(absorbed_lease_count, 1)
        )

        # Logistic-style mapping: ratio of 1.0 (supply equals absorption) maps
        # to ~0.5; ratios >> 1 collapse toward 0; ratios << 1 push toward 1.
        constraint_score = 1.0 / (1.0 + supply_to_absorption_ratio)

        return round(constraint_score, 4)
