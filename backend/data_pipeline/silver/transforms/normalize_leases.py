from __future__ import annotations

from datetime import date

from sqlalchemy.ext.asyncio import AsyncSession

from backend.data_pipeline.silver.schemas.leases import LeaseRecord


def _parse_date(value: str | None) -> date | None:
    if not value:
        return None
    return date.fromisoformat(value)


class LeaseNormalizer:
    """Normalizes raw lease data from NYC DHCR into LeaseRecord shape."""

    @staticmethod
    def normalize_from_dhcr(raw_payload: dict) -> dict:
        return {
            "signed_rent": raw_payload.get("signed_rent", 0),
            "lease_start_date": _parse_date(raw_payload.get("lease_start")),
            "lease_end_date": _parse_date(raw_payload.get("lease_end")),
            "concessions": raw_payload.get("concessions"),
        }

    @staticmethod
    async def persist_normalized_lease(
        session: AsyncSession, normalized_data: dict
    ) -> LeaseRecord:
        new_record = LeaseRecord(**normalized_data)
        session.add(new_record)
        return new_record
