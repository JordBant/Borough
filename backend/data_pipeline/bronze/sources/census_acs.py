from __future__ import annotations

from datetime import datetime, timezone

from backend.data_pipeline.config.settings import EnvironmentSettings
from backend.data_pipeline.config.constants import DataSourceName
from backend.data_pipeline.bronze.clients.government_api_client import GovernmentApiClient

BASE_URL_TEMPLATE = "https://api.census.gov/data/{year}/acs/acs5"

# ACS variable codes for the fields we care about
VARIABLE_MEDIAN_HOUSEHOLD_INCOME = "B19013_001E"
VARIABLE_TOTAL_POPULATION = "B01003_001E"
VARIABLE_HOUSEHOLD_COUNT = "B11001_001E"
VARIABLE_MIGRATION_NET = "B07001_001E"


class CensusAcsExtractor(GovernmentApiClient):
    """Extract American Community Survey data from the Census Bureau API."""

    def __init__(self, settings: EnvironmentSettings) -> None:
        super().__init__(settings, DataSourceName.CENSUS_ACS)

    async def extract_raw_data(self, **kwargs: object) -> dict:
        year = str(
            kwargs.get("year", datetime.now(timezone.utc).year - 1)
        )
        zip_code = str(kwargs.get("zip_code", "11215"))

        url = BASE_URL_TEMPLATE.format(year=year)
        variable_list = ",".join([
            VARIABLE_MEDIAN_HOUSEHOLD_INCOME,
            VARIABLE_TOTAL_POPULATION,
            VARIABLE_HOUSEHOLD_COUNT,
            VARIABLE_MIGRATION_NET,
        ])

        query_parameters = {
            "get": variable_list,
            "for": f"zip code tabulation area:{zip_code}",
        }

        response_data = await self.execute_government_request(
            url,
            query_parameters=query_parameters,
        )
        return {"year": year, "zip_code": zip_code, "records": response_data}
