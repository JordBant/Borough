from __future__ import annotations

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.data_pipeline.gold.features.property_level import (
    RentPerSquareFootCalculator,
    FairMarketRentDeltaCalculator,
    BuildingQualityScoreCalculator,
    OwnershipDurationCalculator,
    TransitAccessScoreCalculator,
    PermitActivityScoreCalculator,
)
from backend.data_pipeline.gold.features.submarket_level import (
    VacancyCompressionCalculator,
    RentGrowthMomentumCalculator,
    MortgageSpilloverIndexCalculator,
    AffordabilityRatioCalculator,
    NeighborhoodComplaintDensityCalculator,
    SupplyConstraintScoreCalculator,
)
from backend.data_pipeline.silver.schemas.properties import PropertyRecord
from backend.data_pipeline.silver.schemas.submarkets import SubmarketRecord


class FeatureStoreWriter:

    def __init__(self) -> None:
        self._property_level_calculators: dict[str, object] = {
            "rent_per_square_foot": RentPerSquareFootCalculator(),
            "fair_market_rent_delta": FairMarketRentDeltaCalculator(),
            "building_quality_score": BuildingQualityScoreCalculator(),
            "ownership_duration": OwnershipDurationCalculator(),
            "transit_access_score": TransitAccessScoreCalculator(),
            "permit_activity_score": PermitActivityScoreCalculator(),
        }
        self._submarket_level_calculators: dict[str, object] = {
            "vacancy_compression": VacancyCompressionCalculator(),
            "rent_growth_momentum": RentGrowthMomentumCalculator(),
            "mortgage_spillover_index": MortgageSpilloverIndexCalculator(),
            "affordability_ratio": AffordabilityRatioCalculator(),
            "neighborhood_complaint_density": NeighborhoodComplaintDensityCalculator(),
            "supply_constraint_score": SupplyConstraintScoreCalculator(),
        }

    async def compute_and_store_property_features(
        self,
        session: AsyncSession,
        property_id: UUID,
    ) -> dict[str, float | None]:
        feature_values: dict[str, float | None] = {}
        for feature_name, calculator in self._property_level_calculators.items():
            feature_values[feature_name] = await calculator.compute(
                session, property_id
            )
        return feature_values

    async def compute_and_store_submarket_features(
        self,
        session: AsyncSession,
        submarket_id: UUID,
    ) -> dict[str, float | None]:
        feature_values: dict[str, float | None] = {}
        for feature_name, calculator in self._submarket_level_calculators.items():
            feature_values[feature_name] = await calculator.compute(
                session, submarket_id
            )
        return feature_values

    async def refresh_all_features(self, session: AsyncSession) -> None:
        all_property_ids_result = await session.execute(
            select(PropertyRecord.property_id)
        )
        property_ids = [row[0] for row in all_property_ids_result.all()]

        for property_id in property_ids:
            await self.compute_and_store_property_features(session, property_id)

        all_submarket_ids_result = await session.execute(
            select(SubmarketRecord.submarket_id)
        )
        submarket_ids = [row[0] for row in all_submarket_ids_result.all()]

        for submarket_id in submarket_ids:
            await self.compute_and_store_submarket_features(session, submarket_id)
