from __future__ import annotations

from abc import ABC, abstractmethod
from datetime import datetime, timezone

from backend.data_pipeline.config.settings import EnvironmentSettings
from backend.data_pipeline.config.constants import DataSourceName
from backend.data_pipeline.config.extract_gate import ExtractGate, RequestParameters


class BaseExtractionClient(ABC):
    """Abstract base for every bronze-layer extraction client.

    Holds a reference to the shared ``ExtractGate`` for centralized HTTP execution
    (retries, backoff, API key injection by ``DataSourceName``). Subclasses
    implement ``extract_raw_data`` and typically call :meth:`execute_get_request`
    or ``self.gate.post`` for network I/O.
    """

    def __init__(
        self,
        settings: EnvironmentSettings,
        source_name: DataSourceName,
    ) -> None:
        self.settings = settings
        self.source_name = source_name
        self.gate = ExtractGate.from_settings(settings)

    async def __aenter__(self) -> BaseExtractionClient:
        await self.gate.__aenter__()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None:  # noqa: ANN001
        await self.gate.__aexit__(exc_type, exc_val, exc_tb)

    async def execute_get_request(
        self,
        url: str,
        query_parameters: dict[str, str] | None = None,
        headers: dict[str, str] | None = None,
    ) -> dict | list:
        """GET via ExtractGate with API key resolved from ``self.source_name``."""

        parameters = RequestParameters(
            query_params=query_parameters or {},
            headers=headers or {},
        )
        return await self.gate.extract(
            url=url,
            source=self.source_name,
            parameters=parameters,
        )
 
    @abstractmethod
    async def extract_raw_data(self, **kwargs: object) -> dict:
        """Fetch raw data from the external source. Subclasses must implement."""

    def build_bronze_envelope(self, payload: dict) -> dict:
        """Wrap a raw payload in the standard bronze envelope format."""
        return {
            "source": self.source_name.value,
            "fetched_at": datetime.now(timezone.utc).isoformat(),
            "payload": payload,
        }
