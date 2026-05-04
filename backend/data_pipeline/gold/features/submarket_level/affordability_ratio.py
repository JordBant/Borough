from __future__ import annotations

from datetime import date
from uuid import UUID

from sqlalchemy import select, func, text
from sqlalchemy.ext.asyncio import AsyncSession

from backend.data_pipeline.silver.schemas.submarkets import SubmarketRecord
from backend.data_pipeline.silver.schemas.fair_market_rents import FairMarketRentRecord


class AffordabilityRatioCalculator:
    """Ratio of annualized median FMR two-bedroom rent to median household
    income for the submarket's zip code.

    Uses HUD Fair Market Rent data and Census ACS median household income.
    """

    async def compute(self, session: AsyncSession, submarket_id: UUID) -> float | None:
        zip_code_statement = (
            select(SubmarketRecord.zip_code)
            .where(SubmarketRecord.submarket_id == submarket_id)
        )
        zip_result = await session.execute(zip_code_statement)
        zip_code = zip_result.scalar_one_or_none()
        if zip_code is None:
            return None

        current_year = date.today().year
        fmr_statement = (
            select(FairMarketRentRecord.two_bedroom_rent)
            .where(
                FairMarketRentRecord.zip_code == zip_code,
                FairMarketRentRecord.year <= current_year,
            )
            .order_by(FairMarketRentRecord.year.desc())
            .limit(1)
        )
        fmr_result = await session.execute(fmr_statement)
        two_bedroom_rent = fmr_result.scalar_one_or_none()
        if two_bedroom_rent is None:
            return None

        try:
            income_statement = text(
                "SELECT median_household_income FROM census_acs "
                "WHERE zip_code = :zip_code LIMIT 1"
            )
            income_result = await session.execute(
                income_statement, {"zip_code": zip_code}
            )
            median_household_income = income_result.scalar_one_or_none()
        except Exception:
            return None

        if not median_household_income:
            return None

        annual_rent = float(two_bedroom_rent) * 12
        return round(annual_rent / float(median_household_income), 4)
