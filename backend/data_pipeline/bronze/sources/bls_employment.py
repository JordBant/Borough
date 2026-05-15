from __future__ import annotations

from datetime import datetime, timezone

from backend.data_pipeline.config.settings import EnvironmentSettings
from backend.data_pipeline.config.constants import DataSourceName
from backend.data_pipeline.config.extract_gate import RequestParameters
from backend.data_pipeline.bronze.clients.base_client import BaseExtractionClient

BASE_URL = "https://api.bls.gov/publicAPI/v2/timeseries/data/"

BROOKLYN_UNEMPLOYMENT_SERIES = "LAUCN360470000000003"
BROOKLYN_EMPLOYMENT_SERIES = "LAUCN360470000000005"


class BlsEmploymentExtractor(BaseExtractionClient):
    """Extract employment and unemployment data from the BLS API.

    BLS v2 uses POST with a JSON body. The ExtractGate handles retry logic
    and auto-injects the registrationkey into the request body.
    """

    def __init__(self, settings: EnvironmentSettings) -> None:
        super().__init__(settings, DataSourceName.BLS_EMPLOYMENT)

    async def extract_raw_data(self, **kwargs: object) -> dict:
        current_year = datetime.now(timezone.utc).year
        start_year = str(kwargs.get("start_year", current_year - 1))
        end_year = str(kwargs.get("end_year", current_year))
        series_ids = kwargs.get("series_ids") or [
            BROOKLYN_UNEMPLOYMENT_SERIES,
            BROOKLYN_EMPLOYMENT_SERIES,
        ]

        request_body = {
            "seriesid": series_ids,
            "startyear": start_year,
            "endyear": end_year,
        }

        parameters = RequestParameters(body=request_body)

        response_data = await self.gate.post(
            url=BASE_URL,
            source=self.source_name,
            parameters=parameters,
        )
        return response_data  # type: ignore[return-value]
