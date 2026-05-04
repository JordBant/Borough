from __future__ import annotations

from collections import Counter
from datetime import date

from sqlalchemy.ext.asyncio import AsyncSession

from backend.data_pipeline.config.constants import DataSourceName
from backend.data_pipeline.silver.schemas.neighborhood_signals import NeighborhoodSignalRecord


class NeighborhoodSignalNormalizer:
    """Aggregates 311 complaint data into NeighborhoodSignalRecord shape."""

    @staticmethod
    def normalize_from_311_complaints(
        raw_complaints: list[dict],
        zip_code: str,
        period_start: date,
        period_end: date,
    ) -> list[dict]:
        counts_by_type: Counter[str] = Counter()
        for complaint in raw_complaints:
            complaint_type = complaint.get("complaint_type", "unknown")
            counts_by_type[complaint_type] += 1

        return [
            {
                "zip_code": zip_code,
                "complaint_type": complaint_type,
                "complaint_count": count,
                "period_start": period_start,
                "period_end": period_end,
                "source": DataSourceName.NYC_311_COMPLAINTS.value,
            }
            for complaint_type, count in counts_by_type.items()
        ]

    @staticmethod
    async def persist_normalized_signal(
        session: AsyncSession, normalized_data: dict
    ) -> NeighborhoodSignalRecord:
        new_record = NeighborhoodSignalRecord(**normalized_data)
        session.add(new_record)
        return new_record
