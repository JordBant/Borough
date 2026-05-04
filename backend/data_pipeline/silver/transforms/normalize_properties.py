from __future__ import annotations

from datetime import date

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.data_pipeline.silver.schemas.properties import PropertyRecord


class PropertyNormalizer:
    """Normalizes raw property data from NYC MapPLUTO into PropertyRecord shape."""

    @staticmethod
    def normalize_from_pluto(raw_pluto_payload: dict) -> dict:
        return {
            "address": raw_pluto_payload.get("address", ""),
            "parcel_id": raw_pluto_payload.get("parcel_id"),
            "latitude": raw_pluto_payload.get("latitude"),
            "longitude": raw_pluto_payload.get("longitude"),
            "year_built": raw_pluto_payload.get("year_built"),
            "bedrooms": None,
            "bathrooms": None,
            "square_footage": raw_pluto_payload.get("lot_area"),
        }

    @staticmethod
    async def persist_normalized_property(
        session: AsyncSession, normalized_data: dict
    ) -> PropertyRecord:
        """Upsert a property record, matching on address or parcel_id."""
        existing_record = None

        if normalized_data.get("parcel_id"):
            result = await session.execute(
                select(PropertyRecord).where(
                    PropertyRecord.parcel_id == normalized_data["parcel_id"]
                )
            )
            existing_record = result.scalars().first()

        if existing_record is None and normalized_data.get("address"):
            result = await session.execute(
                select(PropertyRecord).where(
                    PropertyRecord.address == normalized_data["address"]
                )
            )
            existing_record = result.scalars().first()

        if existing_record is not None:
            for field_name, value in normalized_data.items():
                if value is not None:
                    setattr(existing_record, field_name, value)
            return existing_record

        new_record = PropertyRecord(**normalized_data)
        session.add(new_record)
        return new_record
