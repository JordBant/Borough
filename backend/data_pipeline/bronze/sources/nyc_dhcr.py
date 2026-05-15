from __future__ import annotations

from backend.data_pipeline.config.settings import EnvironmentSettings
from backend.data_pipeline.config.constants import DataSourceName
from backend.data_pipeline.bronze.clients.base_client import BaseExtractionClient

# NYC Open Data Socrata endpoint for DHCR rent-stabilized buildings
BASE_URL = "https://data.cityofnewyork.us/resource/tesw-yqqr.json"


class NycDhcrExtractor(BaseExtractionClient):
    """Extract rent-stabilized building records from NYC DHCR via Socrata."""

    def __init__(self, settings: EnvironmentSettings) -> None:
        super().__init__(settings, DataSourceName.NYC_DHCR)

    async def extract_raw_data(self, **kwargs: object) -> dict:
        zip_code = str(kwargs.get("zip_code", "11215"))
        limit = str(kwargs.get("limit", "1000"))
        offset = str(kwargs.get("offset", "0"))

        query_parameters = {
            "$where": f"postcode='{zip_code}' AND borough='BROOKLYN'",
            "$limit": limit,
            "$offset": offset,
        }

        response_data = await self.execute_get_request(
            BASE_URL,
            query_parameters=query_parameters,
        )
        return {"records": response_data}
