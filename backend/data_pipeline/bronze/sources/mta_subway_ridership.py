from __future__ import annotations

from backend.data_pipeline.config.settings import EnvironmentSettings
from backend.data_pipeline.config.constants import DataSourceName
from backend.data_pipeline.bronze.clients.government_api_client import GovernmentApiClient

BASE_URL = "https://data.ny.gov/resource/wujg-7c2s.json"


class MtaSubwayRidershipExtractor(GovernmentApiClient):
    """Extract MTA subway ridership data from NY State Open Data."""

    def __init__(self, settings: EnvironmentSettings) -> None:
        super().__init__(settings, DataSourceName.MTA_SUBWAY_RIDERSHIP)

    async def extract_raw_data(self, **kwargs: object) -> dict:
        limit = str(kwargs.get("limit", "1000"))
        offset = str(kwargs.get("offset", "0"))
        station = str(kwargs.get("station", ""))
        start_date = str(kwargs.get("start_date", ""))
        end_date = str(kwargs.get("end_date", ""))

        where_clauses: list[str] = []
        if station:
            where_clauses.append(f"station_complex LIKE '%{station}%'")
        if start_date:
            where_clauses.append(f"transit_timestamp >= '{start_date}'")
        if end_date:
            where_clauses.append(f"transit_timestamp <= '{end_date}'")

        query_parameters: dict[str, str] = {
            "$limit": limit,
            "$offset": offset,
            "$order": "transit_timestamp DESC",
        }
        if where_clauses:
            query_parameters["$where"] = " AND ".join(where_clauses)

        response_data = await self.execute_government_request(
            BASE_URL,
            query_parameters=query_parameters,
        )
        return {"records": response_data}
