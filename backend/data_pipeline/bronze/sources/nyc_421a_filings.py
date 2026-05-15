from __future__ import annotations

from backend.data_pipeline.config.settings import EnvironmentSettings
from backend.data_pipeline.config.constants import DataSourceName
from backend.data_pipeline.bronze.clients.base_client import BaseExtractionClient

# NYC Open Data Socrata endpoint for 421-a tax incentive filings
BASE_URL = "https://data.cityofnewyork.us/resource/y7az-s7wc.json"


class Nyc421aFilingsExtractor(BaseExtractionClient):
    """Extract 421-a tax benefit filings for Brooklyn from NYC Open Data."""

    def __init__(self, settings: EnvironmentSettings) -> None:
        super().__init__(settings, DataSourceName.NYC_421A_FILINGS)

    async def extract_raw_data(self, **kwargs: object) -> dict:
        borough = str(kwargs.get("borough", "BROOKLYN"))
        limit = str(kwargs.get("limit", "1000"))
        offset = str(kwargs.get("offset", "0"))

        query_parameters = {
            "$where": f"borough='{borough}'",
            "$limit": limit,
            "$offset": offset,
        }

        response_data = await self.execute_get_request(
            BASE_URL,
            query_parameters=query_parameters,
        )
        return {"records": response_data}
