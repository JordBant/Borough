"""Temporary developer endpoints for hitting each bronze source extractor.

NOT for production. One GET per `*_Extractor` in `backend.data_pipeline.bronze.sources`.
Each route loads `EnvironmentSettings`, runs the extractor inside its async context
manager, and returns a small preview so Swagger / curl responses stay readable.

Mounted under `/dev/sources/...`. Delete this file (and the include in `main.py`)
once a real ingestion path exists.
"""

from __future__ import annotations

import logging
from typing import Any

from fastapi import APIRouter, HTTPException, Query

from backend.data_pipeline.bronze.sources import (
    BlsEmploymentExtractor,
    CensusAcsExtractor,
    FredMortgageRatesExtractor,
    GoogleTrendsExtractor,
    HudFairMarketRentsExtractor,
    MtaSubwayRidershipExtractor,
    Nyc311ComplaintsExtractor,
    Nyc421aFilingsExtractor,
    NycBuildingPermitsExtractor,
    NycDhcrExtractor,
    NycDobJobFilingsExtractor,
    NycDobViolationsExtractor,
    NycHpdLitigationExtractor,
    NycHpdViolationsExtractor,
    NycPlutoExtractor,
    NycRollingSalesExtractor,
)
from backend.data_pipeline.bronze.clients.base_client import BaseExtractionClient
from backend.data_pipeline.config.settings import EnvironmentSettings

logger = logging.getLogger("borough.dev.sources")

dev_source_test_router = APIRouter(
    prefix="/dev/sources",
    tags=["Dev — Source Smoke Tests"],
)

# Cap how much raw data each endpoint echoes back in the HTTP response.
_PREVIEW_RECORD_LIMIT = 5


def _summarize_records(payload: Any) -> tuple[int, list[Any]]:
    """Return ``(count, preview)`` for whichever shape an extractor returned."""

    if isinstance(payload, dict):
        records = payload.get("records")
        if isinstance(records, list):
            return len(records), records[:_PREVIEW_RECORD_LIMIT]
    if isinstance(payload, list):
        return len(payload), payload[:_PREVIEW_RECORD_LIMIT]
    return 0, []


async def _run_extractor(extractor: BaseExtractionClient, **kwargs: Any) -> dict:
    """Open the extractor's gate, call ``extract_raw_data``, return a debug envelope."""

    try:
        async with extractor:
            payload = await extractor.extract_raw_data(**kwargs)
    except Exception as exc:  # noqa: BLE001 — surface upstream errors as HTTP 502
        logger.exception("Extractor %s failed", extractor.source_name.value)
        raise HTTPException(status_code=502, detail=f"{type(exc).__name__}: {exc}") from exc

    record_count, preview = _summarize_records(payload)
    return {
        "source": extractor.source_name.value,
        "kwargs": kwargs,
        "record_count": record_count,
        "preview": preview,
        "raw_keys": list(payload.keys()) if isinstance(payload, dict) else None,
    }


def _settings() -> EnvironmentSettings:
    return EnvironmentSettings.load()


# ---------------------------------------------------------------------------
# NYC Open Data (Socrata)
# ---------------------------------------------------------------------------


@dev_source_test_router.get("/nyc-pluto")
async def test_nyc_pluto(
    zip_code: str = Query("11215"),
    limit: int = Query(50, ge=1, le=1000),
    offset: int = Query(0, ge=0),
) -> dict:
    return await _run_extractor(
        NycPlutoExtractor(_settings()),
        zip_code=zip_code,
        limit=str(limit),
        offset=str(offset),
    )


@dev_source_test_router.get("/nyc-dhcr")
async def test_nyc_dhcr(
    zip_code: str = Query("11215"),
    limit: int = Query(50, ge=1, le=1000),
    offset: int = Query(0, ge=0),
) -> dict:
    return await _run_extractor(
        NycDhcrExtractor(_settings()),
        zip_code=zip_code,
        limit=str(limit),
        offset=str(offset),
    )


@dev_source_test_router.get("/nyc-dob-job-filings")
async def test_nyc_dob_job_filings(
    limit: int = Query(50, ge=1, le=1000),
    offset: int = Query(0, ge=0),
    start_date: str = Query("", description="YYYY-MM-DD"),
    end_date: str = Query("", description="YYYY-MM-DD"),
) -> dict:
    return await _run_extractor(
        NycDobJobFilingsExtractor(_settings()),
        limit=str(limit),
        offset=str(offset),
        start_date=start_date,
        end_date=end_date,
    )


@dev_source_test_router.get("/nyc-dob-violations")
async def test_nyc_dob_violations(
    limit: int = Query(50, ge=1, le=1000),
    offset: int = Query(0, ge=0),
    start_date: str = Query(""),
    end_date: str = Query(""),
) -> dict:
    return await _run_extractor(
        NycDobViolationsExtractor(_settings()),
        limit=str(limit),
        offset=str(offset),
        start_date=start_date,
        end_date=end_date,
    )


@dev_source_test_router.get("/nyc-hpd-violations")
async def test_nyc_hpd_violations(
    limit: int = Query(50, ge=1, le=1000),
    offset: int = Query(0, ge=0),
    violation_class: str = Query("", description="A | B | C"),
    start_date: str = Query(""),
    end_date: str = Query(""),
) -> dict:
    return await _run_extractor(
        NycHpdViolationsExtractor(_settings()),
        limit=str(limit),
        offset=str(offset),
        violation_class=violation_class,
        start_date=start_date,
        end_date=end_date,
    )


@dev_source_test_router.get("/nyc-hpd-litigation")
async def test_nyc_hpd_litigation(
    limit: int = Query(50, ge=1, le=1000),
    offset: int = Query(0, ge=0),
    case_status: str = Query(""),
    case_type: str = Query(""),
) -> dict:
    return await _run_extractor(
        NycHpdLitigationExtractor(_settings()),
        limit=str(limit),
        offset=str(offset),
        case_status=case_status,
        case_type=case_type,
    )


@dev_source_test_router.get("/nyc-building-permits")
async def test_nyc_building_permits(
    borough: str = Query("BROOKLYN"),
    permit_type: str = Query(""),
    limit: int = Query(50, ge=1, le=1000),
    offset: int = Query(0, ge=0),
) -> dict:
    return await _run_extractor(
        NycBuildingPermitsExtractor(_settings()),
        borough=borough,
        permit_type=permit_type,
        limit=str(limit),
        offset=str(offset),
    )


@dev_source_test_router.get("/nyc-421a-filings")
async def test_nyc_421a_filings(
    borough: str = Query("BROOKLYN"),
    limit: int = Query(50, ge=1, le=1000),
    offset: int = Query(0, ge=0),
) -> dict:
    return await _run_extractor(
        Nyc421aFilingsExtractor(_settings()),
        borough=borough,
        limit=str(limit),
        offset=str(offset),
    )


@dev_source_test_router.get("/nyc-rolling-sales")
async def test_nyc_rolling_sales(
    limit: int = Query(50, ge=1, le=1000),
    offset: int = Query(0, ge=0),
) -> dict:
    return await _run_extractor(
        NycRollingSalesExtractor(_settings()),
        limit=str(limit),
        offset=str(offset),
    )


@dev_source_test_router.get("/nyc-311-complaints")
async def test_nyc_311_complaints(
    limit: int = Query(50, ge=1, le=1000),
    offset: int = Query(0, ge=0),
    start_date: str = Query(""),
    end_date: str = Query(""),
    complaint_types: list[str] | None = Query(
        default=None,
        description="Repeat to add multiple, e.g. ?complaint_types=NOISE&complaint_types=PLUMBING",
    ),
) -> dict:
    kwargs: dict[str, Any] = {
        "limit": str(limit),
        "offset": str(offset),
        "start_date": start_date,
        "end_date": end_date,
    }
    if complaint_types:
        kwargs["complaint_types"] = complaint_types
    return await _run_extractor(Nyc311ComplaintsExtractor(_settings()), **kwargs)


# ---------------------------------------------------------------------------
# Federal APIs
# ---------------------------------------------------------------------------


@dev_source_test_router.get("/census-acs")
async def test_census_acs(
    year: int | None = Query(None, description="Defaults to last full year"),
    zip_code: str = Query("11215"),
) -> dict:
    kwargs: dict[str, Any] = {"zip_code": zip_code}
    if year is not None:
        kwargs["year"] = year
    return await _run_extractor(CensusAcsExtractor(_settings()), **kwargs)


@dev_source_test_router.get("/bls-employment")
async def test_bls_employment(
    start_year: int | None = Query(None),
    end_year: int | None = Query(None),
) -> dict:
    kwargs: dict[str, Any] = {}
    if start_year is not None:
        kwargs["start_year"] = start_year
    if end_year is not None:
        kwargs["end_year"] = end_year
    return await _run_extractor(BlsEmploymentExtractor(_settings()), **kwargs)


@dev_source_test_router.get("/fred-mortgage-rates")
async def test_fred_mortgage_rates(
    series_id: str = Query("MORTGAGE30US"),
    observation_start: str = Query("2020-01-01"),
    observation_end: str = Query(""),
) -> dict:
    return await _run_extractor(
        FredMortgageRatesExtractor(_settings()),
        series_id=series_id,
        observation_start=observation_start,
        observation_end=observation_end,
    )


@dev_source_test_router.get("/hud-fair-market-rents")
async def test_hud_fair_market_rents(
    entity_id: str = Query("METRO35620M35620", description="Defaults to NYC metro"),
    year: int | None = Query(None),
) -> dict:
    kwargs: dict[str, Any] = {"entity_id": entity_id}
    if year is not None:
        kwargs["year"] = year
    return await _run_extractor(HudFairMarketRentsExtractor(_settings()), **kwargs)


# ---------------------------------------------------------------------------
# Other
# ---------------------------------------------------------------------------


@dev_source_test_router.get("/mta-subway-ridership")
async def test_mta_subway_ridership(
    limit: int = Query(50, ge=1, le=1000),
    offset: int = Query(0, ge=0),
    station: str = Query(""),
    start_date: str = Query(""),
    end_date: str = Query(""),
) -> dict:
    return await _run_extractor(
        MtaSubwayRidershipExtractor(_settings()),
        limit=str(limit),
        offset=str(offset),
        station=station,
        start_date=start_date,
        end_date=end_date,
    )


@dev_source_test_router.get("/google-trends")
async def test_google_trends(
    geo_code: str = Query("US-NY"),
    timeframe: str = Query("today 12-m"),
    keywords: list[str] | None = Query(
        default=None,
        description="Repeat to add multiple, e.g. ?keywords=brooklyn+rent&keywords=apartment+brooklyn",
    ),
) -> dict:
    kwargs: dict[str, Any] = {"geo_code": geo_code, "timeframe": timeframe}
    if keywords:
        kwargs["keywords"] = keywords
    return await _run_extractor(GoogleTrendsExtractor(_settings()), **kwargs)
