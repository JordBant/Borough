from __future__ import annotations

from datetime import date, timedelta
from uuid import UUID

import polars
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.data_pipeline.silver.schemas.leases import LeaseRecord
from backend.data_pipeline.silver.schemas.properties import PropertyRecord


_GROWTH_WEIGHTS: dict[int, float] = {
    3: 0.5,
    6: 0.3,
    12: 0.2,
}


class RentGrowthMomentumCalculator:
    """Weighted average of signed-rent growth rates over 3, 6, and 12 months.

    Growth rate for each window is computed as the change in median signed
    rent between the first half and the second half of the window.
    """

    async def compute(self, session: AsyncSession, submarket_id: UUID) -> float | None:
        submarket_property_ids = (
            select(PropertyRecord.property_id)
            .where(PropertyRecord.submarket_id == submarket_id)
        )

        today = date.today()
        twelve_months_ago = today - timedelta(days=365)

        leases_statement = (
            select(LeaseRecord.signed_rent, LeaseRecord.lease_start_date)
            .where(
                LeaseRecord.property_id.in_(submarket_property_ids),
                LeaseRecord.lease_start_date >= twelve_months_ago,
            )
            .order_by(LeaseRecord.lease_start_date)
        )
        leases_result = await session.execute(leases_statement)
        lease_rows = leases_result.all()

        if len(lease_rows) < 2:
            return None

        lease_frame = polars.DataFrame(
            {
                "signed_rent": [float(row[0]) for row in lease_rows],
                "lease_start_date": [row[1] for row in lease_rows],
            }
        )

        weighted_growth = 0.0
        windows_with_data = 0

        for months, weight in _GROWTH_WEIGHTS.items():
            growth_rate = self._compute_growth_for_window(
                lease_frame, today, months
            )
            if growth_rate is not None:
                weighted_growth += weight * growth_rate
                windows_with_data += 1

        if windows_with_data == 0:
            return None

        return round(weighted_growth, 4)

    @staticmethod
    def _compute_growth_for_window(
        lease_frame: polars.DataFrame,
        reference_date: date,
        months: int,
    ) -> float | None:
        window_start = reference_date - timedelta(days=months * 30)
        window_midpoint = reference_date - timedelta(days=(months * 30) // 2)

        early_half = lease_frame.filter(
            (polars.col("lease_start_date") >= window_start)
            & (polars.col("lease_start_date") < window_midpoint)
        )
        late_half = lease_frame.filter(
            (polars.col("lease_start_date") >= window_midpoint)
            & (polars.col("lease_start_date") <= reference_date)
        )

        if early_half.is_empty() or late_half.is_empty():
            return None

        early_median = early_half["signed_rent"].median()
        late_median = late_half["signed_rent"].median()

        if early_median is None or early_median == 0:
            return None

        return (late_median - early_median) / early_median
