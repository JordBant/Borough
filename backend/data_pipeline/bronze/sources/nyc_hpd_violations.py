from __future__ import annotations

from backend.data_pipeline.config.settings import EnvironmentSettings
from backend.data_pipeline.config.constants import DataSourceName
from backend.data_pipeline.bronze.clients.base_client import BaseExtractionClient

BASE_URL = "https://data.cityofnewyork.us/resource/wvxf-dwi5.json"

BROOKLYN_BOROUGH_ID = "3"

VALID_VIOLATION_CLASSES = {"A", "B", "C"}


class NycHpdViolationsExtractor(BaseExtractionClient):
    """Extract HPD housing violation records for Brooklyn from NYC Open Data."""

    def __init__(self, settings: EnvironmentSettings) -> None:
        super().__init__(settings, DataSourceName.NYC_HPD_VIOLATIONS)

    async def extract_raw_data(self, **kwargs: object) -> dict:
        limit = str(kwargs.get("limit", "1000"))
        offset = str(kwargs.get("offset", "0"))
        violation_class = str(kwargs.get("violation_class", ""))
        start_date = str(kwargs.get("start_date", ""))
        end_date = str(kwargs.get("end_date", ""))

        where_clauses = [f"boroid='{BROOKLYN_BOROUGH_ID}'"]
        if violation_class and violation_class.upper() in VALID_VIOLATION_CLASSES:
            where_clauses.append(f"class='{violation_class.upper()}'")
        if start_date:
            where_clauses.append(f"inspectiondate >= '{start_date}'")
        if end_date:
            where_clauses.append(f"inspectiondate <= '{end_date}'")

        query_parameters = {
            "$where": " AND ".join(where_clauses),
            "$limit": limit,
            "$offset": offset,
            "$order": "inspectiondate DESC",
        }

        response_data = await self.execute_get_request(
            BASE_URL,
            query_parameters=query_parameters,
        )
        return {"records": response_data}
