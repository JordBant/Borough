from __future__ import annotations

from datetime import date
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.data_pipeline.silver.schemas.leases import LeaseRecord
from backend.data_pipeline.silver.schemas.properties import PropertyRecord
from backend.data_pipeline.silver.schemas.fair_market_rents import FairMarketRentRecord
from backend.data_pipeline.silver.schemas.submarkets import SubmarketRecord

_BEDROOM_COUNT_TO_FMR_COLUMN = {
    0: FairMarketRentRecord.efficiency_rent,
    1: FairMarketRentRecord.one_bedroom_rent,
    2: FairMarketRentRecord.two_bedroom_rent,
    3: FairMarketRentRecord.three_bedroom_rent,
    4: FairMarketRentRecord.four_bedroom_rent,
}


class FairMarketRentDeltaCalculator:
    """Compares the property's latest signed rent against the HUD Fair Market
    Rent for the same bedroom count and zip code.

    Returns the delta (signed_rent - fair_market_rent). A positive value
    means the property rents above FMR.
    """

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
            select(PropertyRecord.bedrooms, PropertyRecord.submarket_id)
            .where(PropertyRecord.property_id == property_id)
        )
        property_result = await session.execute(property_statement)
        property_row = property_result.one_or_none()
        if property_row is None:
            return None

        bedroom_count, submarket_id = property_row
        if bedroom_count is None or submarket_id is None:
            return None

        zip_code_statement = (
            select(SubmarketRecord.zip_code)
            .where(SubmarketRecord.submarket_id == submarket_id)
        )
        zip_result = await session.execute(zip_code_statement)
        zip_code = zip_result.scalar_one_or_none()
        if zip_code is None:
            return None

        fmr_column = _BEDROOM_COUNT_TO_FMR_COLUMN.get(
            min(bedroom_count, 4)
        )

        current_year = date.today().year
        fmr_statement = (
            select(fmr_column)
            .where(
                FairMarketRentRecord.zip_code == zip_code,
                FairMarketRentRecord.year <= current_year,
            )
            .order_by(FairMarketRentRecord.year.desc())
            .limit(1)
        )
        fmr_result = await session.execute(fmr_statement)
        fair_market_rent = fmr_result.scalar_one_or_none()
        if fair_market_rent is None:
            return None

        return float(signed_rent) - float(fair_market_rent)
