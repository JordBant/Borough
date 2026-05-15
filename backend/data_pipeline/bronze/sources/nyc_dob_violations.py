from __future__ import annotations

from backend.data_pipeline.config.settings import EnvironmentSettings
from backend.data_pipeline.config.constants import DataSourceName
from backend.data_pipeline.bronze.clients.base_client import BaseExtractionClient

BASE_URL = "https://data.cityofnewyork.us/resource/3h2n-5cm9.json"

BROOKLYN_BOROUGH_CODE = "3"


class NycDobViolationsExtractor(BaseExtractionClient):
    """Extract DOB violation records for Brooklyn from NYC Open Data."""

    def __init__(self, settings: EnvironmentSettings) -> None:
        super().__init__(settings, DataSourceName.NYC_DOB_VIOLATIONS)

    async def extract_raw_data(self, **kwargs: object) -> dict:
        limit = str(kwargs.get("limit", "1000"))
        offset = str(kwargs.get("offset", "0"))
        start_date = str(kwargs.get("start_date", ""))
        end_date = str(kwargs.get("end_date", ""))

        where_clauses = [f"boro='{BROOKLYN_BOROUGH_CODE}'"]
        if start_date:
            where_clauses.append(f"issue_date >= '{start_date}'")
        if end_date:
            where_clauses.append(f"issue_date <= '{end_date}'")

        query_parameters = {
            "$where": " AND ".join(where_clauses),
            "$limit": limit,
            "$offset": offset,
            "$order": "issue_date DESC",
        }

        response_data = await self.execute_get_request(
            BASE_URL,
            query_parameters=query_parameters,
        )
        return {"records": response_data}
