from __future__ import annotations

import asyncio
import logging
from dataclasses import dataclass, field
from typing import Any

import httpx

from backend.data_pipeline.config.constants import DataSourceName

logger = logging.getLogger(__name__)

_DEFAULT_TIMEOUT_SECONDS = 60.0
_DEFAULT_MAX_RETRIES = 3
_INITIAL_BACKOFF_SECONDS = 2.0


# ---------------------------------------------------------------------------
# Maps each DataSourceName to the environment variable that holds its key.
# Sources sharing the same key (e.g. all NYC Open Data sources use one token)
# are grouped under the same env var.
# ---------------------------------------------------------------------------

_SOURCE_TO_ENV_KEY: dict[DataSourceName, str] = {
    DataSourceName.NYC_PLUTO: "NYC_OPEN_DATA_APP_TOKEN",
    DataSourceName.NYC_DHCR: "NYC_OPEN_DATA_APP_TOKEN",
    DataSourceName.NYC_DOB_JOB_FILINGS: "NYC_OPEN_DATA_APP_TOKEN",
    DataSourceName.NYC_DOB_VIOLATIONS: "NYC_OPEN_DATA_APP_TOKEN",
    DataSourceName.NYC_HPD_VIOLATIONS: "NYC_OPEN_DATA_APP_TOKEN",
    DataSourceName.NYC_HPD_LITIGATION: "NYC_OPEN_DATA_APP_TOKEN",
    DataSourceName.NYC_BUILDING_PERMITS: "NYC_OPEN_DATA_APP_TOKEN",
    DataSourceName.NYC_421A_FILINGS: "NYC_OPEN_DATA_APP_TOKEN",
    DataSourceName.NYC_ROLLING_SALES: "NYC_OPEN_DATA_APP_TOKEN",
    DataSourceName.NYC_311_COMPLAINTS: "NYC_OPEN_DATA_APP_TOKEN",
    DataSourceName.CENSUS_ACS: "CENSUS_API_KEY",
    DataSourceName.BLS_EMPLOYMENT: "BLS_API_KEY",
    DataSourceName.FRED_MORTGAGE_RATES: "FRED_API_KEY",
    DataSourceName.HUD_FAIR_MARKET_RENTS: "FRED_API_KEY",
    DataSourceName.MTA_SUBWAY_RIDERSHIP: "NYC_OPEN_DATA_APP_TOKEN",
    DataSourceName.GOOGLE_TRENDS: "",
}

# Maps each source to the query parameter name its API expects for auth.
# The ExtractGate auto-injects the resolved key under this param name.
_SOURCE_KEY_PARAM_NAME: dict[DataSourceName, str] = {
    DataSourceName.NYC_PLUTO: "$$app_token",
    DataSourceName.NYC_DHCR: "$$app_token",
    DataSourceName.NYC_DOB_JOB_FILINGS: "$$app_token",
    DataSourceName.NYC_DOB_VIOLATIONS: "$$app_token",
    DataSourceName.NYC_HPD_VIOLATIONS: "$$app_token",
    DataSourceName.NYC_HPD_LITIGATION: "$$app_token",
    DataSourceName.NYC_BUILDING_PERMITS: "$$app_token",
    DataSourceName.NYC_421A_FILINGS: "$$app_token",
    DataSourceName.NYC_ROLLING_SALES: "$$app_token",
    DataSourceName.NYC_311_COMPLAINTS: "$$app_token",
    DataSourceName.MTA_SUBWAY_RIDERSHIP: "$$app_token",
    DataSourceName.CENSUS_ACS: "key",
    DataSourceName.BLS_EMPLOYMENT: "registrationkey",
    DataSourceName.FRED_MORTGAGE_RATES: "api_key",
    DataSourceName.HUD_FAIR_MARKET_RENTS: "api_key",
    DataSourceName.GOOGLE_TRENDS: "",
}


@dataclass
class RequestParameters:
    """Optional configuration passed alongside the target URL."""

    query_params: dict[str, str] = field(default_factory=dict)
    headers: dict[str, str] = field(default_factory=dict)
    body: dict[str, Any] | None = None
    timeout_seconds: float = _DEFAULT_TIMEOUT_SECONDS
    max_retries: int = _DEFAULT_MAX_RETRIES


class ExtractGate:
    """Centralized HTTP execution layer for all source extraction.

    Encapsulates retry logic, backoff, timeout management, and provider-based
    API key resolution. Every bronze extractor delegates its network calls
    through this single gate.

    Usage:
        gate = ExtractGate.from_settings(settings)
        async with gate:
            data = await gate.extract(
                url="https://api.census.gov/data/2023/acs/acs5",
                source=DataSourceName.CENSUS_ACS,
                parameters=RequestParameters(query_params={"get": "B19013_001E"}),
            )
    """

    def __init__(self, api_keys: dict[str, str]) -> None:
        self._api_keys = api_keys
        self._client: httpx.AsyncClient | None = None

    @classmethod
    def from_settings(cls, settings: Any) -> ExtractGate:
        """Build an ExtractGate from an EnvironmentSettings instance.

        Reads every known API key field from settings at construction time,
        making keys available for runtime lookup by source name.
        """
        from backend.data_pipeline.config.settings import EnvironmentSettings

        if not isinstance(settings, EnvironmentSettings):
            raise TypeError("Expected an EnvironmentSettings instance")

        keys: dict[str, str] = {
            "FRED_API_KEY": settings.fred_api_key,
            "CENSUS_API_KEY": settings.census_api_key,
            "BLS_API_KEY": settings.bls_api_key,
            "NYC_OPEN_DATA_APP_TOKEN": settings.nyc_open_data_app_token,
        }
        return cls(api_keys=keys)

    # ------------------------------------------------------------------
    # Context manager — manages the shared httpx.AsyncClient lifecycle
    # ------------------------------------------------------------------

    async def __aenter__(self) -> ExtractGate:
        self._client = httpx.AsyncClient(
            timeout=httpx.Timeout(_DEFAULT_TIMEOUT_SECONDS),
            follow_redirects=True,
        )
        return self

    async def __aexit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        if self._client:
            await self._client.aclose()
            self._client = None

    # ------------------------------------------------------------------
    # API key resolution
    # ------------------------------------------------------------------

    def resolve_api_key(self, source: DataSourceName) -> str | None:
        """Look up the API key for the given provider.

        Returns the key value if configured, or None if the source has no
        key registered or the key environment variable was left empty.
        This consolidates the old _require/_optional split into one method
        that always checks availability without raising.
        """
        env_var_name = _SOURCE_TO_ENV_KEY.get(source, "")
        if not env_var_name:
            return None
        value = self._api_keys.get(env_var_name, "")
        return value if value else None

    # ------------------------------------------------------------------
    # Core request execution
    # ------------------------------------------------------------------

    async def extract(
        self,
        url: str,
        source: DataSourceName,
        parameters: RequestParameters | None = None,
    ) -> dict | list:
        """Execute an HTTP GET extraction with retries and exponential backoff.

        Args:
            url: The target endpoint URL.
            source: Which data source this request is for. Used to resolve
                    the API key at request time.
            parameters: Optional RequestParameters with query params, headers,
                        timeout, and retry configuration.

        Returns:
            Parsed JSON response (dict or list).

        Raises:
            RuntimeError: If all retry attempts are exhausted.
        """
        if self._client is None:
            raise RuntimeError(
                "ExtractGate HTTP client not initialised — use 'async with' context manager"
            )

        params = parameters or RequestParameters()
        max_retries = params.max_retries
        timeout = httpx.Timeout(params.timeout_seconds)

        api_key = self.resolve_api_key(source)
        merged_query_params = dict(params.query_params) if params.query_params else {}
        merged_headers = dict(params.headers) if params.headers else {}

        if api_key:
            key_param_name = _SOURCE_KEY_PARAM_NAME.get(source, "")
            if key_param_name and key_param_name not in merged_query_params:
                merged_query_params[key_param_name] = api_key
            logger.debug("API key injected for source %s as '%s'", source.value, key_param_name)

        last_exception: Exception | None = None
        for attempt in range(max_retries):
            try:
                response = await self._client.get(
                    url,
                    params=merged_query_params or None,
                    headers=merged_headers or None,
                    timeout=timeout,
                )
                response.raise_for_status()
                return response.json()
            except (httpx.HTTPStatusError, httpx.TransportError) as exc:
                last_exception = exc
                wait_seconds = _INITIAL_BACKOFF_SECONDS * (2 ** attempt)
                logger.warning(
                    "ExtractGate attempt %d/%d failed for %s [%s]: %s — retrying in %.1fs",
                    attempt + 1,
                    max_retries,
                    source.value,
                    url,
                    exc,
                    wait_seconds,
                )
                await asyncio.sleep(wait_seconds)

        raise RuntimeError(
            f"All {max_retries} ExtractGate attempts failed for {source.value} at {url}"
        ) from last_exception

    async def post(
        self,
        url: str,
        source: DataSourceName,
        parameters: RequestParameters | None = None,
    ) -> dict | list:
        """Execute an HTTP POST request with retries and exponential backoff.

        Args:
            url: The target endpoint URL.
            source: Which data source this request is for. Used to resolve
                    the API key at request time.
            parameters: Optional RequestParameters. The `body` field is sent
                        as JSON. If the source has an API key configured, it
                        is injected into the body under the source's key param name.

        Returns:
            Parsed JSON response (dict or list).

        Raises:
            RuntimeError: If all retry attempts are exhausted.
        """
        if self._client is None:
            raise RuntimeError(
                "ExtractGate HTTP client not initialised — use 'async with' context manager"
            )

        params = parameters or RequestParameters()
        max_retries = params.max_retries
        timeout = httpx.Timeout(params.timeout_seconds)

        api_key = self.resolve_api_key(source)
        request_body = dict(params.body) if params.body else {}
        merged_headers = dict(params.headers) if params.headers else {}

        if api_key:
            key_param_name = _SOURCE_KEY_PARAM_NAME.get(source, "")
            if key_param_name and key_param_name not in request_body:
                request_body[key_param_name] = api_key

        if "Content-Type" not in merged_headers:
            merged_headers["Content-Type"] = "application/json"

        last_exception: Exception | None = None
        for attempt in range(max_retries):
            try:
                response = await self._client.post(
                    url,
                    json=request_body or None,
                    headers=merged_headers or None,
                    timeout=timeout,
                )
                response.raise_for_status()
                return response.json()
            except (httpx.HTTPStatusError, httpx.TransportError) as exc:
                last_exception = exc
                wait_seconds = _INITIAL_BACKOFF_SECONDS * (2 ** attempt)
                logger.warning(
                    "ExtractGate POST attempt %d/%d failed for %s [%s]: %s — retrying in %.1fs",
                    attempt + 1,
                    max_retries,
                    source.value,
                    url,
                    exc,
                    wait_seconds,
                )
                await asyncio.sleep(wait_seconds)

        raise RuntimeError(
            f"All {max_retries} ExtractGate POST attempts failed for {source.value} at {url}"
        ) from last_exception
