from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.data_pipeline.silver.schemas.submarkets import SubmarketRecord


class SubmarketNormalizer:
    """Normalizes submarket-level data from Census/BLS and building permits."""

    @staticmethod
    def normalize_from_census(
        raw_census_payload: dict, raw_bls_payload: dict
    ) -> dict:
        unemployment_rate = raw_bls_payload.get("unemployment_rate")
        # Rough proxy: negative unemployment change signals job growth
        job_growth_rate = (
            (1.0 - unemployment_rate / 100.0) if unemployment_rate is not None else None
        )

        return {
            "zip_code": raw_census_payload.get("zip_code", ""),
            "neighborhood": raw_census_payload.get("neighborhood", ""),
            "vacancy_rate": None,
            "job_growth_rate": job_growth_rate,
            "supply_pipeline_units": None,
        }

    @staticmethod
    def normalize_from_permits(raw_permit_payload: dict) -> dict:
        return {
            "zip_code": raw_permit_payload.get("zip_code", ""),
            "neighborhood": raw_permit_payload.get("neighborhood", ""),
            "vacancy_rate": None,
            "job_growth_rate": None,
            "supply_pipeline_units": raw_permit_payload.get("residential_units"),
        }

    @staticmethod
    async def persist_normalized_submarket(
        session: AsyncSession, normalized_data: dict
    ) -> SubmarketRecord:
        """Upsert a submarket record, matching on zip_code."""
        existing_record = None

        if normalized_data.get("zip_code"):
            result = await session.execute(
                select(SubmarketRecord).where(
                    SubmarketRecord.zip_code == normalized_data["zip_code"]
                )
            )
            existing_record = result.scalars().first()

        if existing_record is not None:
            for field_name, value in normalized_data.items():
                if value is not None:
                    setattr(existing_record, field_name, value)
            return existing_record

        new_record = SubmarketRecord(**normalized_data)
        session.add(new_record)
        return new_record
