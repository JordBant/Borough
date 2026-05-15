from __future__ import annotations

from backend.data_pipeline.config.settings import EnvironmentSettings
from backend.data_pipeline.config.constants import DataSourceName
from backend.data_pipeline.bronze.clients.base_client import BaseExtractionClient

BASE_URL = "https://data.cityofnewyork.us/resource/59kj-x8nc.json"

BROOKLYN_BOROUGH_ID = "3"


class NycHpdLitigationExtractor(BaseExtractionClient):
    """Extract HPD litigation case records for Brooklyn from NYC Open Data."""

    def __init__(self, settings: EnvironmentSettings) -> None:
        super().__init__(settings, DataSourceName.NYC_HPD_LITIGATION)

    async def extract_raw_data(self, **kwargs: object) -> dict:
        limit = str(kwargs.get("limit", "1000"))
        offset = str(kwargs.get("offset", "0"))
        case_status = str(kwargs.get("case_status", ""))
        case_type = str(kwargs.get("case_type", ""))

        where_clauses = [f"boroid='{BROOKLYN_BOROUGH_ID}'"]
        if case_status:
            where_clauses.append(f"status='{case_status}'")
        if case_type:
            where_clauses.append(f"casetype='{case_type}'")

        query_parameters = {
            "$where": " AND ".join(where_clauses),
            "$limit": limit,
            "$offset": offset,
            "$order": "caseopendate DESC",
        }

        response_data = await self.execute_get_request(
            BASE_URL,
            query_parameters=query_parameters,
        )
        return {"records": response_data}
