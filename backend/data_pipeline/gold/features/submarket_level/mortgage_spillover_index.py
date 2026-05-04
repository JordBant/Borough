from __future__ import annotations

from datetime import date, timedelta
from uuid import UUID

import polars
from sqlalchemy import select, func, extract
from sqlalchemy.ext.asyncio import AsyncSession

from backend.data_pipeline.silver.schemas.listings import ListingRecord
from backend.data_pipeline.silver.schemas.properties import PropertyRecord


class MortgageSpilloverIndexCalculator:
    """Correlates mortgage rate changes with listing volume in the submarket.

    Requires a `fred_mortgage_rates` table with (observation_date, rate_30yr_fixed).
    Returns None when mortgage rate data is unavailable.
    """

    async def compute(self, session: AsyncSession, submarket_id: UUID) -> float | None:
        submarket_property_ids = (
            select(PropertyRecord.property_id)
            .where(PropertyRecord.submarket_id == submarket_id)
        )

        today = date.today()
        twelve_months_ago = today - timedelta(days=365)

        monthly_listing_volume_statement = (
            select(
                extract("year", ListingRecord.list_date).label("listing_year"),
                extract("month", ListingRecord.list_date).label("listing_month"),
                func.count().label("listing_count"),
            )
            .where(
                ListingRecord.property_id.in_(submarket_property_ids),
                ListingRecord.list_date >= twelve_months_ago,
            )
            .group_by("listing_year", "listing_month")
            .order_by("listing_year", "listing_month")
        )
        volume_result = await session.execute(monthly_listing_volume_statement)
        volume_rows = volume_result.all()

        if len(volume_rows) < 3:
            return None

        # FRED mortgage rate data is not yet in the silver layer.
        # When the table is added, query monthly average rates here and
        # compute the Pearson correlation between rate changes and volume changes.
        try:
            from sqlalchemy import text

            rate_statement = text(
                "SELECT date_trunc('month', observation_date) AS rate_month, "
                "AVG(rate_30yr_fixed) AS average_rate "
                "FROM fred_mortgage_rates "
                "WHERE observation_date >= :cutoff "
                "GROUP BY rate_month ORDER BY rate_month"
            )
            rate_result = await session.execute(
                rate_statement, {"cutoff": twelve_months_ago}
            )
            rate_rows = rate_result.all()
        except Exception:
            return None

        if len(rate_rows) < 3:
            return None

        volume_frame = polars.DataFrame(
            {
                "year": [int(row[0]) for row in volume_rows],
                "month": [int(row[1]) for row in volume_rows],
                "listing_count": [int(row[2]) for row in volume_rows],
            }
        ).with_columns(
            polars.col("listing_count").diff().alias("volume_change")
        )

        rate_frame = polars.DataFrame(
            {
                "rate_month": [row[0] for row in rate_rows],
                "average_rate": [float(row[1]) for row in rate_rows],
            }
        ).with_columns(
            polars.col("average_rate").diff().alias("rate_change")
        )

        volume_changes = volume_frame.drop_nulls("volume_change")["volume_change"]
        rate_changes = rate_frame.drop_nulls("rate_change")["rate_change"]

        alignment_length = min(len(volume_changes), len(rate_changes))
        if alignment_length < 2:
            return None

        correlation = polars.pearson_corr(
            volume_changes.head(alignment_length),
            rate_changes.head(alignment_length),
        )

        if correlation is None:
            return None

        return round(float(correlation), 4)
