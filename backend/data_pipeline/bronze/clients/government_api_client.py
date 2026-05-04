from __future__ import annotations

import abc

from backend.data_pipeline.config.settings import EnvironmentSettings
from backend.data_pipeline.config.constants import DataSourceName
from backend.data_pipeline.config.extract_gate import RequestParameters
from backend.data_pipeline.bronze.clients.base_client import BaseExtractionClient


class GovernmentApiClient(BaseExtractionClient, abc.ABC):
    """Extraction client for government and public-sector API endpoints.

    Delegates all HTTP execution to the shared ExtractGate. Subclasses call
    execute_government_request() which injects the appropriate API key and
    routes through the centralized retry/backoff logic.
    """

    def __init__(
        self,
        settings: EnvironmentSettings,
        source_name: DataSourceName,
    ) -> None:
        super().__init__(settings, source_name)

    async def execute_government_request(
        self,
        url: str,
        query_parameters: dict[str, str] | None = None,
        headers: dict[str, str] | None = None,
    ) -> dict | list:
        """Send a GET request to a government API through the ExtractGate.

        The API key for this source is resolved and injected automatically
        at request time based on self.source_name.
        """
        parameters = RequestParameters(
            query_params=query_parameters or {},
            headers=headers or {},
        )
        return await self.gate.extract(
            url=url,
            source=self.source_name,
            parameters=parameters,
        )
