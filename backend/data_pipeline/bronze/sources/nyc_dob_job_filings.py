from __future__ import annotations

from backend.data_pipeline.config.settings import EnvironmentSettings
from backend.data_pipeline.config.constants import DataSourceName
from backend.data_pipeline.bronze.clients.base_client import BaseExtractionClient

BASE_URL = "https://data.cityofnewyork.us/resource/ic3t-wcy2.json"

BROOKLYN_BOROUGH_CODE = "3"


class NycDobJobFilingsExtractor(BaseExtractionClient):
    """Extract DOB job filing records for Brooklyn from NYC Open Data."""

    def __init__(self, settings: EnvironmentSettings) -> None:
        super().__init__(settings, DataSourceName.NYC_DOB_JOB_FILINGS)

    async def extract_raw_data(self, **kwargs: object) -> dict:
        limit = str(kwargs.get("limit", "1000"))
        offset = str(kwargs.get("offset", "0"))
        start_date = str(kwargs.get("start_date", ""))
        end_date = str(kwargs.get("end_date", ""))

        where_clauses = [
            f"boro='{BROOKLYN_BOROUGH_CODE}'",
            "residentialunits IS NOT NULL AND residentialunits > '0'",
        ]
        if start_date:
            where_clauses.append(f"latestactiondate >= '{start_date}'")
        if end_date:
            where_clauses.append(f"latestactiondate <= '{end_date}'")

        query_parameters = {
            "$where": " AND ".join(where_clauses),
            "$limit": limit,
            "$offset": offset,
            "$order": "latestactiondate DESC",
        }

        response_data = await self.execute_get_request(
            BASE_URL,
            query_parameters=query_parameters,
        )
        return {"records": response_data}
