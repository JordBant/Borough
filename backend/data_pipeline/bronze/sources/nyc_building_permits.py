from __future__ import annotations

from backend.data_pipeline.config.settings import EnvironmentSettings
from backend.data_pipeline.config.constants import DataSourceName
from backend.data_pipeline.bronze.clients.base_client import BaseExtractionClient

BASE_URL = "https://data.cityofnewyork.us/resource/ipu4-2vj7.json"


class NycBuildingPermitsExtractor(BaseExtractionClient):
    """Extract building permit data for Brooklyn from NYC Open Data."""

    def __init__(self, settings: EnvironmentSettings) -> None:
        super().__init__(settings, DataSourceName.NYC_BUILDING_PERMITS)

    async def extract_raw_data(self, **kwargs: object) -> dict:
        borough = str(kwargs.get("borough", "BROOKLYN"))
        permit_type = str(kwargs.get("permit_type", ""))
        limit = str(kwargs.get("limit", "1000"))
        offset = str(kwargs.get("offset", "0"))

        where_clauses = [f"borough='{borough}'"]
        if permit_type:
            where_clauses.append(f"permit_type='{permit_type}'")

        query_parameters = {
            "$where": " AND ".join(where_clauses),
            "$limit": limit,
            "$offset": offset,
            "$order": "filing_date DESC",
        }

        response_data = await self.execute_get_request(
            BASE_URL,
            query_parameters=query_parameters,
        )
        return {"records": response_data}
