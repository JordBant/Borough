from __future__ import annotations

import math
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.data_pipeline.silver.schemas.properties import PropertyRecord
from backend.data_pipeline.silver.schemas.transit_access import TransitAccessRecord

_DISTANCE_TIERS: list[tuple[float, float]] = [
    (0.25, 1.0),
    (0.50, 0.8),
    (0.75, 0.5),
    (1.00, 0.3),
]
_BEYOND_ONE_MILE_SCORE = 0.1

_DEGREES_PER_MILE_LATITUDE = 1.0 / 69.0
_DEGREES_PER_MILE_LONGITUDE_NYC = 1.0 / 53.0


def _euclidean_distance_miles(
    latitude_a: float,
    longitude_a: float,
    latitude_b: float,
    longitude_b: float,
) -> float:
    """Approximate Euclidean distance in miles using NYC-appropriate
    degree-to-mile conversions."""
    delta_latitude_miles = (latitude_a - latitude_b) / _DEGREES_PER_MILE_LATITUDE
    delta_longitude_miles = (longitude_a - longitude_b) / _DEGREES_PER_MILE_LONGITUDE_NYC
    return math.sqrt(delta_latitude_miles ** 2 + delta_longitude_miles ** 2)


class TransitAccessScoreCalculator:
    """Scores transit accessibility based on distance to the nearest
    subway station.

    <0.25 mi = 1.0, <0.5 mi = 0.8, <0.75 mi = 0.5, <1.0 mi = 0.3,
    >1.0 mi = 0.1.
    """

    async def compute(self, session: AsyncSession, property_id: UUID) -> float | None:
        property_statement = (
            select(PropertyRecord.latitude, PropertyRecord.longitude)
            .where(PropertyRecord.property_id == property_id)
        )
        property_result = await session.execute(property_statement)
        property_row = property_result.one_or_none()
        if property_row is None:
            return None

        property_latitude, property_longitude = property_row
        if property_latitude is None or property_longitude is None:
            return None

        stations_statement = select(
            TransitAccessRecord.latitude,
            TransitAccessRecord.longitude,
        )
        stations_result = await session.execute(stations_statement)
        station_rows = stations_result.all()

        if not station_rows:
            return None

        nearest_distance = min(
            _euclidean_distance_miles(
                float(property_latitude),
                float(property_longitude),
                float(station_latitude),
                float(station_longitude),
            )
            for station_latitude, station_longitude in station_rows
        )

        for distance_threshold, score in _DISTANCE_TIERS:
            if nearest_distance < distance_threshold:
                return score

        return _BEYOND_ONE_MILE_SCORE
