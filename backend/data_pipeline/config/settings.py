from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path

from dotenv import load_dotenv

from backend.data_pipeline.config.constants import DataSourceName

_ENV_LOADED = False


def _ensure_env_loaded() -> None:
    global _ENV_LOADED
    if _ENV_LOADED:
        return
    backend_dir = Path(__file__).resolve().parents[2]
    env_path = backend_dir / ".env"
    if not env_path.exists():
        env_path = backend_dir / "data_pipeline" / ".env"
    if env_path.exists():
        load_dotenv(dotenv_path=env_path)
    _ENV_LOADED = True


@dataclass(frozen=True)
class EnvironmentSettings:
    """Single point of truth for every environment variable the pipeline needs.

    All data sources are free / public.  The keys below are optional tokens
    that increase rate limits but are NOT required for basic access.
    """

    # --- Government / public API keys (all free to obtain) ---
    fred_api_key: str = field(default="")
    census_api_key: str = field(default="")
    bls_api_key: str = field(default="")
    nyc_open_data_app_token: str = field(default="")

    # --- S3 (Bronze ingestion bucket) ---
    bronze_s3_region: str = field(default="us-east-1")
    bronze_s3_bucket: str = field(default="borough-bronze")
    bronze_s3_access_key: str = field(default="")
    bronze_s3_secret_key: str = field(default="")

    # --- Postgres ---
    postgres_dsn: str = field(default="postgresql+asyncpg://borough:borough@localhost:5432/borough")

    # --- Redis ---
    redis_url: str = field(default="redis://localhost:6379/0")

    # ------------------------------------------------------------------
    # Unified API key resolution
    # ------------------------------------------------------------------

    _SOURCE_KEY_MAPPING: dict[str, str] = field(
        default_factory=lambda: {
            "nyc_pluto": "nyc_open_data_app_token",
            "nyc_dhcr": "nyc_open_data_app_token",
            "nyc_dob_job_filings": "nyc_open_data_app_token",
            "nyc_dob_violations": "nyc_open_data_app_token",
            "nyc_hpd_violations": "nyc_open_data_app_token",
            "nyc_hpd_litigation": "nyc_open_data_app_token",
            "nyc_building_permits": "nyc_open_data_app_token",
            "nyc_421a_filings": "nyc_open_data_app_token",
            "nyc_rolling_sales": "nyc_open_data_app_token",
            "nyc_311_complaints": "nyc_open_data_app_token",
            "mta_subway_ridership": "nyc_open_data_app_token",
            "census_acs": "census_api_key",
            "bls_employment": "bls_api_key",
            "fred_mortgage_rates": "fred_api_key",
            "hud_fair_market_rents": "fred_api_key",
            "google_trends": "",
        },
        repr=False,
    )

    def api_key_for_source(self, source: DataSourceName) -> str | None:
        """Resolve the API key for any data source provider.

        Replaces the previous _require/_optional split with a single lookup
        that always checks availability. Returns the key string if configured,
        or None if the source has no associated key or the key is empty.
        """
        attribute_name = self._SOURCE_KEY_MAPPING.get(source.value, "")
        if not attribute_name:
            return None
        value = getattr(self, attribute_name, "")
        return value if value else None

    # ------------------------------------------------------------------
    # Factory
    # ------------------------------------------------------------------

    @classmethod
    def load(cls) -> EnvironmentSettings:
        """Load settings from environment variables (reads .env file once)."""
        _ensure_env_loaded()
        return cls(
            fred_api_key=os.getenv("FRED_API_KEY", ""),
            census_api_key=os.getenv("CENSUS_API_KEY", ""),
            bls_api_key=os.getenv("BLS_API_KEY", ""),
            nyc_open_data_app_token=os.getenv("NYC_OPEN_DATA_APP_TOKEN", ""),
            bronze_s3_region=os.getenv("BRONZE_S3_REGION", "us-east-1"),
            bronze_s3_bucket=os.getenv("BRONZE_S3_BUCKET", "borough-bronze"),
            bronze_s3_access_key=os.getenv("BRONZE_S3_ACCESS_KEY", ""),
            bronze_s3_secret_key=os.getenv("BRONZE_S3_SECRET_KEY", ""),
            postgres_dsn=os.getenv(
                "POSTGRES_DSN",
                "postgresql+asyncpg://borough:borough@localhost:5432/borough",
            ),
            redis_url=os.getenv("REDIS_URL", "redis://localhost:6379/0"),
        )
