# Gold Layer — Feature Store

## Overview

The gold layer computes pre-aggregated features from normalized silver data, consumed by the Rent Pressure Score (RPS) engine and forecasting models. All features are derived exclusively from **free public data**, using a composite "truth through overlap" model that cross-validates multiple independent sources.

## Feature Organization

### Property-Level Features (`features/property_level/`)

Computed per-property using silver-layer data:

| Feature | Calculator Class | Description |
|---|---|---|
| Rent per sqft | `RentPerSquareFootCalculator` | Latest DHCR signed rent divided by PLUTO square footage |
| Fair market rent delta | `FairMarketRentDeltaCalculator` | Property's signed rent minus HUD FMR for same bedroom count and zip code. Positive = above FMR. |
| Building quality score | `BuildingQualityScoreCalculator` | Score (0.0–1.0) from DOB + HPD violation counts in trailing 24 months. Weights: HPD class C = 3x, class B = 2x, class A = 1x, DOB = 1.5x. 1.0 = no violations. |
| Ownership duration | `OwnershipDurationCalculator` | Years since building was constructed (from PLUTO `year_built`). Serves as proxy until rolling sales transfer data is integrated. |
| Transit access score | `TransitAccessScoreCalculator` | Euclidean distance to nearest MTA subway station. Scores: <0.25mi = 1.0, <0.5mi = 0.8, <0.75mi = 0.5, <1mi = 0.3, >1mi = 0.1. |
| Permit activity score | `PermitActivityScoreCalculator` | DOB violation filings in the property's submarket over trailing 12 months, relative to borough-wide average. Combined with supply pipeline data. Returns 0.0–1.0. |

### Submarket-Level Features (`features/submarket_level/`)

Computed per-submarket using borough-wide aggregations:

| Feature | Calculator Class | Description |
|---|---|---|
| Vacancy compression | `VacancyCompressionCalculator` | Submarket vacancy rate vs borough-wide average from Census ACS data |
| Rent growth momentum | `RentGrowthMomentumCalculator` | Weighted DHCR signed-rent growth at 3/6/12-month intervals using polars |
| Mortgage spillover index | `MortgageSpilloverIndexCalculator` | Pearson correlation between FRED mortgage rate changes and listing volume changes |
| Affordability ratio | `AffordabilityRatioCalculator` | Annualized HUD FMR two-bedroom rent / Census ACS median household income for the submarket's zip code |
| Neighborhood complaint density | `NeighborhoodComplaintDensityCalculator` | 311 complaint volume for the submarket in trailing 6 months, normalized against borough-wide average. Returns 0.0–1.0. |
| Supply constraint score | `SupplyConstraintScoreCalculator` | Permitted new units vs lease absorption rate. High supply + low absorption = low constraint (0.0). |

## Feature Store Writer

`FeatureStoreWriter` in `store/feature_store.py` orchestrates computation:

- `compute_and_store_property_features(session, property_id)` — runs all 6 property calculators
- `compute_and_store_submarket_features(session, submarket_id)` — runs all 6 submarket calculators
- `refresh_all_features(session)` — iterates all properties and submarkets for a full refresh cycle

## Interface

Every calculator follows the same async interface: `async compute(session, entity_id) -> float | None`, returning `None` when insufficient data is available.

## Source Attribution

Each computed feature tracks which bronze sources contributed to its value via the `source_confidence` schema in the silver layer. This enables transparency into which free data sources informed any given score.
