from __future__ import annotations

from backend.data_pipeline.config.settings import EnvironmentSettings
from backend.data_pipeline.config.constants import DataSourceName
from backend.data_pipeline.bronze.clients.government_api_client import GovernmentApiClient

BASE_URL = "https://api.stlouisfed.org/fred/series/observations"

# FRED series ID for 30-year fixed mortgage rate
SERIES_30YR_FIXED_MORTGAGE = "MORTGAGE30US"


class FredMortgageRatesExtractor(GovernmentApiClient):
    """Extract 30-year fixed mortgage rate observations from the FRED API."""

    def __init__(self, settings: EnvironmentSettings) -> None:
        super().__init__(settings, DataSourceName.FRED_MORTGAGE_RATES)

    async def extract_raw_data(self, **kwargs: object) -> dict:
        series_id = str(kwargs.get("series_id", SERIES_30YR_FIXED_MORTGAGE))
        observation_start = str(kwargs.get("observation_start", "2020-01-01"))
        observation_end = str(kwargs.get("observation_end", ""))

        query_parameters: dict[str, str] = {
            "series_id": series_id,
            "file_type": "json",
            "observation_start": observation_start,
        }
        if observation_end:
            query_parameters["observation_end"] = observation_end

        response_data = await self.execute_government_request(
            BASE_URL,
            query_parameters=query_parameters,
        )
        return response_data
