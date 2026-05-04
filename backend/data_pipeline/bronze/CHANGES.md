# Bronze Layer — Raw Data Lake

## Overview

The bronze layer is the immutable extraction tier of the medallion architecture. Raw payloads from every external source land here **untouched**, enabling full replay and audit of any downstream transformation.

All 16 data sources are **free and publicly accessible**. The architecture follows a "truth through overlap" strategy — combining multiple independent free sources to cross-validate data points and assign confidence scores.

## Storage

- **Target:** S3-compatible object storage (MinIO for local development, AWS S3 for production)
- **Format:** JSON envelopes keyed by `{source}/{YYYY}/{MM}/{DD}/{uuid}.json`
- **Immutability:** Bronze data is append-only. No records are mutated or deleted.

## Client Abstractions

Three extraction client types, each inheriting from `BaseExtractionClient` (`clients/base_client.py`):

| Client | Module | Purpose |
|---|---|---|
| `GovernmentApiClient` | `clients/government_api_client.py` | NYC Open Data Socrata endpoints and state-level APIs (MTA). Supports app tokens as query params. 60s timeout, 3 retries with exponential backoff. |
| `FederalApiClient` | `clients/federal_api_client.py` | Federal agency APIs (Census, BLS, FRED, HUD). Same retry/timeout pattern as GovernmentApiClient but separated for clarity. |
| `WebScraperClient` | `clients/web_scraper_client.py` | Playwright-based headless browser for JS-heavy pages. Available as an abstraction but not actively used by any current source. |

`BaseExtractionClient` provides:
- Consistent constructor accepting `EnvironmentSettings` and `DataSourceName`
- `build_bronze_envelope()` to wrap payloads in the standard bronze format: `{"source": ..., "fetched_at": ..., "payload": ...}`

## Source Extractors

### NYC Open Data (Socrata API) — 10 sources

| Source | Module | Endpoint ID |
|---|---|---|
| MapPLUTO | `sources/nyc_pluto.py` | Property lot attributes, zoning, building class |
| DHCR Rent Stabilized | `sources/nyc_dhcr.py` | `tesw-yqqr` — rent-stabilized building records |
| DOB Job Filings | `sources/nyc_dob_job_filings.py` | `ic3t-wcy2` — new building and alteration filings |
| DOB Violations | `sources/nyc_dob_violations.py` | `3h2n-5cm9` — building code violations |
| HPD Violations | `sources/nyc_hpd_violations.py` | `wvxf-dwi5` — housing maintenance violations (class A/B/C) |
| HPD Litigation | `sources/nyc_hpd_litigation.py` | `59kj-x8nc` — housing court cases |
| Building Permits | `sources/nyc_building_permits.py` | `ipu4-2vj7` — issued construction permits |
| 421-a Filings | `sources/nyc_421a_filings.py` | `y7az-s7wc` — tax abatement program filings |
| Rolling Sales | `sources/nyc_rolling_sales.py` | `usep-8jbt` — annualized property sale records |
| 311 Complaints | `sources/nyc_311_complaints.py` | `erm2-nwe9` — noise, heat, building complaints |

### Federal APIs — 4 sources

| Source | Module | Endpoint |
|---|---|---|
| Census ACS | `sources/census_acs.py` | `api.census.gov` — income, population, housing |
| BLS Employment | `sources/bls_employment.py` | `api.bls.gov` — local area unemployment/employment |
| FRED Mortgage Rates | `sources/fred_mortgage_rates.py` | `api.stlouisfed.org` — 30-year fixed rate series |
| HUD Fair Market Rents | `sources/hud_fair_market_rents.py` | `huduser.gov` — FMR by metro/zip and bedroom count |

### Transit — 1 source

| Source | Module | Endpoint |
|---|---|---|
| MTA Subway Ridership | `sources/mta_subway_ridership.py` | `data.ny.gov` (`wujg-7c2s`) — station-level ridership |

### Library — 1 source

| Source | Module | Method |
|---|---|---|
| Google Trends | `sources/google_trends.py` | `pytrends` library — search interest signals |

## Source Confidence Scoring

Each source has a confidence weight (0–100) defined in `SOURCE_CONFIDENCE_SCORES` in `config/constants.py`. Government records (PLUTO, DOB, HPD, DHCR) score 90–95. Federal data (FRED, Census) scores 85–95. Google Trends scores 50. These weights drive the "truth through overlap" composite model in the gold layer.

## Environment Variables

All API keys are loaded through `EnvironmentSettings.load()` in `config/settings.py` — the single point of truth for environment configuration. Every key is **free** and **optional** (they improve rate limits but are not required for basic access).
