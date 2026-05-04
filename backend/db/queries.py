from __future__ import annotations

from uuid import UUID

from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncSession

from backend.data_pipeline.silver.schemas.properties import PropertyRecord
from backend.data_pipeline.silver.schemas.submarkets import SubmarketRecord
from backend.data_pipeline.silver.schemas.leases import LeaseRecord
from backend.data_pipeline.silver.schemas.building_violations import BuildingViolationRecord
from backend.data_pipeline.silver.schemas.property_sales import PropertySaleRecord
from backend.data_pipeline.silver.schemas.fair_market_rents import FairMarketRentRecord
from backend.data_pipeline.silver.schemas.source_confidence import SourceConfidenceRecord
from backend.data_pipeline.silver.schemas.rps_scores import RentPressureScoreRecord


class PropertyQueries:
    """Read queries for property-level data."""

    @staticmethod
    async def get_property_by_id(
        session: AsyncSession, property_id: UUID
    ) -> PropertyRecord | None:
        result = await session.execute(
            select(PropertyRecord).where(
                PropertyRecord.property_id == property_id
            )
        )
        return result.scalars().first()

    @staticmethod
    async def get_properties_by_submarket(
        session: AsyncSession, submarket_id: UUID
    ) -> list[PropertyRecord]:
        result = await session.execute(
            select(PropertyRecord).where(
                PropertyRecord.submarket_id == submarket_id
            )
        )
        return list(result.scalars().all())

    @staticmethod
    async def get_property_by_bbl(
        session: AsyncSession, parcel_id: str
    ) -> PropertyRecord | None:
        result = await session.execute(
            select(PropertyRecord).where(
                PropertyRecord.parcel_id == parcel_id
            )
        )
        return result.scalars().first()


class SubmarketQueries:
    """Read queries for submarket-level data."""

    @staticmethod
    async def get_submarket_by_id(
        session: AsyncSession, submarket_id: UUID
    ) -> SubmarketRecord | None:
        result = await session.execute(
            select(SubmarketRecord).where(
                SubmarketRecord.submarket_id == submarket_id
            )
        )
        return result.scalars().first()

    @staticmethod
    async def get_submarket_by_zip(
        session: AsyncSession, zip_code: str
    ) -> SubmarketRecord | None:
        result = await session.execute(
            select(SubmarketRecord).where(
                SubmarketRecord.zip_code == zip_code
            )
        )
        return result.scalars().first()

    @staticmethod
    async def get_all_submarkets(session: AsyncSession) -> list[SubmarketRecord]:
        result = await session.execute(select(SubmarketRecord))
        return list(result.scalars().all())


class LeaseQueries:
    """Read queries for lease/comp data."""

    @staticmethod
    async def get_leases_for_property(
        session: AsyncSession, property_id: UUID
    ) -> list[LeaseRecord]:
        result = await session.execute(
            select(LeaseRecord)
            .where(LeaseRecord.property_id == property_id)
            .order_by(LeaseRecord.lease_start_date.desc())
        )
        return list(result.scalars().all())


class ScoreQueries:
    """Read queries for RPS scores and source confidence."""

    @staticmethod
    async def get_latest_rps_score(
        session: AsyncSession, property_id: UUID
    ) -> RentPressureScoreRecord | None:
        result = await session.execute(
            select(RentPressureScoreRecord)
            .where(RentPressureScoreRecord.property_id == property_id)
            .order_by(RentPressureScoreRecord.computed_at.desc())
            .limit(1)
        )
        return result.scalars().first()

    @staticmethod
    async def get_source_confidence_for_property(
        session: AsyncSession, property_id: UUID
    ) -> list[SourceConfidenceRecord]:
        result = await session.execute(
            select(SourceConfidenceRecord).where(
                SourceConfidenceRecord.property_id == property_id
            )
        )
        return list(result.scalars().all())


class FeatureQueries:
    """Read queries for gold-layer computed features.

    Features are stored as rows in the gold feature tables. This class
    provides access to the computed values without importing the
    calculators themselves.
    """

    @staticmethod
    async def get_property_features(
        session: AsyncSession, property_id: UUID
    ) -> dict[str, float | None]:
        """Retrieve all computed property-level features for a given property."""
        statement = text(
            "SELECT feature_name, feature_value FROM property_features "
            "WHERE property_id = :property_id"
        )
        result = await session.execute(statement, {"property_id": str(property_id)})
        return {row[0]: row[1] for row in result.all()}

    @staticmethod
    async def get_submarket_features(
        session: AsyncSession, submarket_id: UUID
    ) -> dict[str, float | None]:
        """Retrieve all computed submarket-level features."""
        statement = text(
            "SELECT feature_name, feature_value FROM submarket_features "
            "WHERE submarket_id = :submarket_id"
        )
        result = await session.execute(statement, {"submarket_id": str(submarket_id)})
        return {row[0]: row[1] for row in result.all()}
