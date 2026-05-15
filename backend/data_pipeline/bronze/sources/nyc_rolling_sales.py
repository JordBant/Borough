from __future__ import annotations

from backend.data_pipeline.config.settings import EnvironmentSettings
from backend.data_pipeline.config.constants import DataSourceName
from backend.data_pipeline.bronze.clients.base_client import BaseExtractionClient

BASE_URL = "https://data.cityofnewyork.us/resource/usep-8jbt.json"

BROOKLYN_BOROUGH_CODE = "3"

RESIDENTIAL_BUILDING_CLASSES = (
    "A", "B", "C", "D", "R",
)


class NycRollingSalesExtractor(BaseExtractionClient):
    """Extract rolling property sales for Brooklyn from NYC Open Data."""

    def __init__(self, settings: EnvironmentSettings) -> None:
        super().__init__(settings, DataSourceName.NYC_ROLLING_SALES)

    async def extract_raw_data(self, **kwargs: object) -> dict:
        limit = str(kwargs.get("limit", "1000"))
        offset = str(kwargs.get("offset", "0"))

        class_prefix_filters = " OR ".join(
            f"building_class_at_time_of_sale LIKE '{prefix}%'"
            for prefix in RESIDENTIAL_BUILDING_CLASSES
        )

        query_parameters = {
            "$where": (
                f"borough='{BROOKLYN_BOROUGH_CODE}'"
                f" AND ({class_prefix_filters})"
            ),
            "$limit": limit,
            "$offset": offset,
            "$order": "sale_date DESC",
        }

        response_data = await self.execute_get_request(
            BASE_URL,
            query_parameters=query_parameters,
        )
        return {"records": response_data}
