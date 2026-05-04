from __future__ import annotations

from enum import Enum
from typing import Literal, TypedDict


# ---------------------------------------------------------------------------
# Data source names — every source in the pipeline is free and publicly
# accessible.  The enum value is the canonical key used in bronze envelopes,
# silver source columns, and confidence-score lookups.
# ---------------------------------------------------------------------------

class DataSourceName(str, Enum):
    # NYC Open Data — Housing & Buildings
    NYC_PLUTO = "nyc_pluto"
    NYC_DHCR = "nyc_dhcr"
    NYC_DOB_JOB_FILINGS = "nyc_dob_job_filings"
    NYC_DOB_VIOLATIONS = "nyc_dob_violations"
    NYC_HPD_VIOLATIONS = "nyc_hpd_violations"
    NYC_HPD_LITIGATION = "nyc_hpd_litigation"
    NYC_BUILDING_PERMITS = "nyc_building_permits"
    NYC_421A_FILINGS = "nyc_421a_filings"

    # NYC Open Data — Property Sales & Neighborhood
    NYC_ROLLING_SALES = "nyc_rolling_sales"
    NYC_311_COMPLAINTS = "nyc_311_complaints"

    # Federal — Demographics & Economics
    CENSUS_ACS = "census_acs"
    BLS_EMPLOYMENT = "bls_employment"
    FRED_MORTGAGE_RATES = "fred_mortgage_rates"

    # Federal — Housing
    HUD_FAIR_MARKET_RENTS = "hud_fair_market_rents"

    # Transit
    MTA_SUBWAY_RIDERSHIP = "mta_subway_ridership"

    # Search demand
    GOOGLE_TRENDS = "google_trends"


DataSourceLiteral = Literal[
    "nyc_pluto",
    "nyc_dhcr",
    "nyc_dob_job_filings",
    "nyc_dob_violations",
    "nyc_hpd_violations",
    "nyc_hpd_litigation",
    "nyc_building_permits",
    "nyc_421a_filings",
    "nyc_rolling_sales",
    "nyc_311_complaints",
    "census_acs",
    "bls_employment",
    "fred_mortgage_rates",
    "hud_fair_market_rents",
    "mta_subway_ridership",
    "google_trends",
]


class DataSourceType(str, Enum):
    """Classifies how data is retrieved from each source."""
    GOVERNMENT_API = "government_api"
    FEDERAL_API = "federal_api"
    OPEN_DATA_LIBRARY = "open_data_library"


DATA_SOURCE_TYPE_REGISTRY: dict[DataSourceName, DataSourceType] = {
    DataSourceName.NYC_PLUTO: DataSourceType.GOVERNMENT_API,
    DataSourceName.NYC_DHCR: DataSourceType.GOVERNMENT_API,
    DataSourceName.NYC_DOB_JOB_FILINGS: DataSourceType.GOVERNMENT_API,
    DataSourceName.NYC_DOB_VIOLATIONS: DataSourceType.GOVERNMENT_API,
    DataSourceName.NYC_HPD_VIOLATIONS: DataSourceType.GOVERNMENT_API,
    DataSourceName.NYC_HPD_LITIGATION: DataSourceType.GOVERNMENT_API,
    DataSourceName.NYC_BUILDING_PERMITS: DataSourceType.GOVERNMENT_API,
    DataSourceName.NYC_421A_FILINGS: DataSourceType.GOVERNMENT_API,
    DataSourceName.NYC_ROLLING_SALES: DataSourceType.GOVERNMENT_API,
    DataSourceName.NYC_311_COMPLAINTS: DataSourceType.GOVERNMENT_API,
    DataSourceName.CENSUS_ACS: DataSourceType.FEDERAL_API,
    DataSourceName.BLS_EMPLOYMENT: DataSourceType.FEDERAL_API,
    DataSourceName.FRED_MORTGAGE_RATES: DataSourceType.FEDERAL_API,
    DataSourceName.HUD_FAIR_MARKET_RENTS: DataSourceType.FEDERAL_API,
    DataSourceName.MTA_SUBWAY_RIDERSHIP: DataSourceType.GOVERNMENT_API,
    DataSourceName.GOOGLE_TRENDS: DataSourceType.OPEN_DATA_LIBRARY,
}


# ---------------------------------------------------------------------------
# Source confidence scores — used for weighted composite models.
# Higher means more authoritative.  Government records trump all.
# ---------------------------------------------------------------------------

SOURCE_CONFIDENCE_SCORES: dict[DataSourceName, int] = {
    DataSourceName.NYC_PLUTO: 95,
    DataSourceName.NYC_DHCR: 95,
    DataSourceName.NYC_DOB_JOB_FILINGS: 90,
    DataSourceName.NYC_DOB_VIOLATIONS: 90,
    DataSourceName.NYC_HPD_VIOLATIONS: 90,
    DataSourceName.NYC_HPD_LITIGATION: 90,
    DataSourceName.NYC_BUILDING_PERMITS: 90,
    DataSourceName.NYC_421A_FILINGS: 90,
    DataSourceName.NYC_ROLLING_SALES: 85,
    DataSourceName.NYC_311_COMPLAINTS: 80,
    DataSourceName.CENSUS_ACS: 90,
    DataSourceName.BLS_EMPLOYMENT: 85,
    DataSourceName.FRED_MORTGAGE_RATES: 95,
    DataSourceName.HUD_FAIR_MARKET_RENTS: 90,
    DataSourceName.MTA_SUBWAY_RIDERSHIP: 85,
    DataSourceName.GOOGLE_TRENDS: 50,
}


# ---------------------------------------------------------------------------
# Brooklyn submarkets
# ---------------------------------------------------------------------------

class BrooklynSubmarket(str, Enum):
    PARK_SLOPE = "park_slope"
    CROWN_HEIGHTS = "crown_heights"
    BUSHWICK = "bushwick"
    WILLIAMSBURG = "williamsburg"
    BAY_RIDGE = "bay_ridge"
    FLATBUSH = "flatbush"
    DUMBO_DOWNTOWN = "dumbo_downtown_brooklyn"


SUBMARKET_ZIP_CODES: dict[BrooklynSubmarket, list[str]] = {
    BrooklynSubmarket.PARK_SLOPE: ["11215", "11217"],
    BrooklynSubmarket.CROWN_HEIGHTS: ["11213", "11216", "11225", "11238"],
    BrooklynSubmarket.BUSHWICK: ["11206", "11221", "11237"],
    BrooklynSubmarket.WILLIAMSBURG: ["11211", "11249"],
    BrooklynSubmarket.BAY_RIDGE: ["11209", "11220", "11228"],
    BrooklynSubmarket.FLATBUSH: ["11226", "11210", "11218"],
    BrooklynSubmarket.DUMBO_DOWNTOWN: ["11201"],
}


# Brooklyn borough code used in NYC Open Data queries
NYC_BOROUGH_CODE_BROOKLYN = "3"
NYC_BOROUGH_NAME_BROOKLYN = "BROOKLYN"


# ---------------------------------------------------------------------------
# Payload shape hints — lightweight TypedDicts describing what each bronze
# source returns before silver normalization.
# ---------------------------------------------------------------------------

class NycPlutoPayload(TypedDict, total=False):
    borough_block_lot: str
    address: str
    owner_name: str
    lot_area: int
    year_built: int
    building_class: str
    residential_units: int
    latitude: float
    longitude: float


class NycDhcrPayload(TypedDict, total=False):
    address: str
    borough: str
    zip_code: str
    building_id: str
    status: str


class NycDobJobFilingPayload(TypedDict, total=False):
    job_number: str
    job_type: str
    borough: str
    block: str
    lot: str
    zip_code: str
    residential_units: int
    filing_date: str
    job_status: str


class NycDobViolationPayload(TypedDict, total=False):
    violation_number: str
    borough_block_lot: str
    violation_type: str
    violation_date: str
    disposition_date: str | None
    penalty_amount: float | None


class NycHpdViolationPayload(TypedDict, total=False):
    violation_id: int
    borough_id: str
    block: str
    lot: str
    address: str
    violation_class: str
    violation_date: str
    status: str


class NycHpdLitigationPayload(TypedDict, total=False):
    litigation_id: int
    borough_id: str
    block: str
    lot: str
    case_type: str
    case_status: str
    case_open_date: str


class NycBuildingPermitPayload(TypedDict, total=False):
    permit_number: str
    job_type: str
    borough: str
    zip_code: str
    residential_units: int
    filing_date: str


class Nyc421aFilingPayload(TypedDict, total=False):
    property_address: str
    borough: str
    expiration_date: str
    tax_benefit_status: str


class NycRollingSalesPayload(TypedDict, total=False):
    borough: str
    block: str
    lot: str
    address: str
    building_class: str
    sale_price: int
    sale_date: str
    residential_units: int
    year_built: int


class Nyc311ComplaintPayload(TypedDict, total=False):
    unique_key: str
    complaint_type: str
    borough: str
    zip_code: str
    latitude: float
    longitude: float
    created_date: str
    status: str


class CensusAcsPayload(TypedDict, total=False):
    zip_code: str
    median_household_income: int
    total_population: int
    migration_net: int
    household_count: int
    renter_occupied_units: int
    vacancy_rate: float


class BlsEmploymentPayload(TypedDict, total=False):
    area_code: str
    period: str
    unemployment_rate: float
    employment_count: int


class FredMortgageRatePayload(TypedDict, total=False):
    observation_date: str
    rate_30yr_fixed: float


class HudFairMarketRentPayload(TypedDict, total=False):
    zip_code: str
    year: int
    efficiency: int
    one_bedroom: int
    two_bedroom: int
    three_bedroom: int
    four_bedroom: int


class MtaSubwayRidershipPayload(TypedDict, total=False):
    station_complex_id: str
    station_name: str
    latitude: float
    longitude: float
    ridership_date: str
    total_ridership: int


class GoogleTrendsPayload(TypedDict, total=False):
    keyword: str
    geo_code: str
    date: str
    interest_over_time: int
