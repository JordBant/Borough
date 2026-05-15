from __future__ import annotations

from backend.data_pipeline.config.settings import EnvironmentSettings
from backend.data_pipeline.config.constants import DataSourceName
from backend.data_pipeline.bronze.clients.base_client import BaseExtractionClient

BASE_URL = "https://data.cityofnewyork.us/resource/erm2-nwe9.json"

HOUSING_COMPLAINT_TYPES = [
    "HEAT/HOT WATER",
    "PLUMBING",
    "PAINT/PLASTER",
    "NOISE",
]


class Nyc311ComplaintsExtractor(BaseExtractionClient):
    """Extract housing-related 311 complaints for Brooklyn from NYC Open Data."""

    def __init__(self, settings: EnvironmentSettings) -> None:
        super().__init__(settings, DataSourceName.NYC_311_COMPLAINTS)

    async def extract_raw_data(self, **kwargs: object) -> dict:
        limit = str(kwargs.get("limit", "1000"))
        offset = str(kwargs.get("offset", "0"))
        complaint_types = kwargs.get("complaint_types") or HOUSING_COMPLAINT_TYPES
        start_date = str(kwargs.get("start_date", ""))
        end_date = str(kwargs.get("end_date", ""))

        type_list: list[str] = list(complaint_types)  # type: ignore[arg-type]
        type_filter = ", ".join(f"'{ct}'" for ct in type_list)

        where_clauses = [
            "borough='BROOKLYN'",
            f"complaint_type IN ({type_filter})",
        ]
        if start_date:
            where_clauses.append(f"created_date >= '{start_date}'")
        if end_date:
            where_clauses.append(f"created_date <= '{end_date}'")

        query_parameters = {
            "$where": " AND ".join(where_clauses),
            "$limit": limit,
            "$offset": offset,
            "$order": "created_date DESC",
        }

        response_data = await self.execute_get_request(
            BASE_URL,
            query_parameters=query_parameters,
        )
        return {"records": response_data}
