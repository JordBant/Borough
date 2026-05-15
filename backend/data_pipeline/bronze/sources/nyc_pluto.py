from __future__ import annotations

from backend.data_pipeline.config.settings import EnvironmentSettings
from backend.data_pipeline.config.constants import DataSourceName
from backend.data_pipeline.bronze.clients.base_client import BaseExtractionClient

# NYC Open Data Socrata endpoint for MapPLUTO
BASE_URL = "https://data.cityofnewyork.us/resource/64uk-42ks.json"


class NycPlutoExtractor(BaseExtractionClient):
    """Extract MapPLUTO parcel data for Brooklyn from NYC Open Data."""

    def __init__(self, settings: EnvironmentSettings) -> None:
        super().__init__(settings, DataSourceName.NYC_PLUTO)

    async def extract_raw_data(self, **kwargs: object) -> dict:
        zip_code = str(kwargs.get("zip_code", "11215"))
        limit = str(kwargs.get("limit", "1000"))
        offset = str(kwargs.get("offset", "0"))

        query_parameters = {
            "$where": f"zipcode='{zip_code}' AND borough='BK'",
            "$limit": limit,
            "$offset": offset,
        }

        response_data = await self.execute_get_request(
            BASE_URL,
            query_parameters=query_parameters,
        )
        return {"records": response_data}
