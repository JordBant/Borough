from __future__ import annotations

from datetime import date

from sqlalchemy.ext.asyncio import AsyncSession

from backend.data_pipeline.config.constants import DataSourceName
from backend.data_pipeline.silver.schemas.building_violations import BuildingViolationRecord


def _parse_date(value: str | None) -> date | None:
    if not value:
        return None
    return date.fromisoformat(value)


class ViolationNormalizer:
    """Normalizes raw violation data from DOB and HPD into BuildingViolationRecord shape."""

    @staticmethod
    def normalize_from_dob(raw_payload: dict) -> dict:
        borough_block_lot = raw_payload.get("borough_block_lot")
        return {
            "source": DataSourceName.NYC_DOB_VIOLATIONS.value,
            "violation_class": raw_payload.get("violation_type", ""),
            "violation_date": _parse_date(raw_payload.get("violation_date")),
            "disposition_date": _parse_date(raw_payload.get("disposition_date")),
            "penalty_amount": raw_payload.get("penalty_amount"),
            "status": raw_payload.get("status", "unknown"),
            "borough_block_lot": borough_block_lot,
        }

    @staticmethod
    def normalize_from_hpd(raw_payload: dict) -> dict:
        borough_id = raw_payload.get("borough_id", "")
        block = raw_payload.get("block", "")
        lot = raw_payload.get("lot", "")
        borough_block_lot = f"{borough_id}-{block}-{lot}" if borough_id else None
        return {
            "source": DataSourceName.NYC_HPD_VIOLATIONS.value,
            "violation_class": raw_payload.get("violation_class", ""),
            "violation_date": _parse_date(raw_payload.get("violation_date")),
            "disposition_date": None,
            "penalty_amount": None,
            "status": raw_payload.get("status", "unknown"),
            "borough_block_lot": borough_block_lot,
        }

    @staticmethod
    async def persist_normalized_violation(
        session: AsyncSession, normalized_data: dict
    ) -> BuildingViolationRecord:
        new_record = BuildingViolationRecord(**normalized_data)
        session.add(new_record)
        return new_record
