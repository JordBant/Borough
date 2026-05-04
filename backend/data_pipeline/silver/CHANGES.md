# Silver Layer — Normalized Postgres

## Overview

The silver layer transforms raw bronze payloads into entity-resolved, schema-enforced records stored in PostgreSQL. Every table uses UUID primary keys and enforces foreign key relationships for referential integrity.

Identity resolution is **BBL-based** (Borough-Block-Lot) — NYC's canonical parcel identifier from PLUTO. Property-level records are linked through BBL or address matching. The `usaddress` library provides fallback parsing for records without BBL.

## Database

- **Engine:** PostgreSQL with async access via SQLAlchemy 2.0 + asyncpg
- **Connection:** `DatabaseConnectionManager` in `database/connection.py` provides lazy engine creation, session factories, and table initialization
- **Base Model:** All schema models inherit from `DatabaseModel` (SQLAlchemy `DeclarativeBase`)

## Schemas

Organized for readability — one file per entity, each in `schemas/`:

| Table | Model | Module | Primary Key |
|---|---|---|---|
| `properties` | `PropertyRecord` | `schemas/properties.py` | `property_id` (UUID) |
| `listings` | `ListingRecord` | `schemas/listings.py` | `listing_id` (UUID) |
| `leases` | `LeaseRecord` | `schemas/leases.py` | `lease_id` (UUID) |
| `submarkets` | `SubmarketRecord` | `schemas/submarkets.py` | `submarket_id` (UUID) |
| `rps_scores` | `RentPressureScoreRecord` | `schemas/rps_scores.py` | `score_id` (UUID) |
| `building_violations` | `BuildingViolationRecord` | `schemas/building_violations.py` | `violation_id` (UUID) |
| `neighborhood_signals` | `NeighborhoodSignalRecord` | `schemas/neighborhood_signals.py` | `signal_id` (UUID) |
| `property_sales` | `PropertySaleRecord` | `schemas/property_sales.py` | `sale_id` (UUID) |
| `transit_access` | `TransitAccessRecord` | `schemas/transit_access.py` | `station_id` (UUID) |
| `fair_market_rents` | `FairMarketRentRecord` | `schemas/fair_market_rents.py` | `record_id` (UUID) |
| `source_confidence` | `SourceConfidenceRecord` | `schemas/source_confidence.py` | `confidence_id` (UUID) |

### Key Relationships

- `listings.property_id` -> `properties.property_id`
- `leases.property_id` -> `properties.property_id`
- `properties.submarket_id` -> `submarkets.submarket_id`
- `rps_scores.property_id` -> `properties.property_id`
- `building_violations.property_id` -> `properties.property_id` (nullable)
- `property_sales.property_id` -> `properties.property_id` (nullable)
- `neighborhood_signals.submarket_id` -> `submarkets.submarket_id` (nullable)
- `source_confidence.property_id` -> `properties.property_id` (nullable)

### Standalone Tables (no FK to properties)

- `transit_access` — station-level records keyed by `station_id`, linked to properties via lat/lng proximity in the gold layer
- `fair_market_rents` — HUD benchmark rents keyed by `zip_code` + `year`, joined to properties via submarket zip codes in the gold layer

## Transforms

Each normalizer maps raw source payloads to the canonical schema shape, handling missing fields gracefully:

| Normalizer | Module | Sources Handled |
|---|---|---|
| `PropertyNormalizer` | `transforms/normalize_properties.py` | NYC MapPLUTO |
| `ListingNormalizer` | `transforms/normalize_listings.py` | Manual entry (broker feeds/approved APIs when available) |
| `LeaseNormalizer` | `transforms/normalize_leases.py` | NYC DHCR rent-stabilized records |
| `SubmarketNormalizer` | `transforms/normalize_submarkets.py` | Census ACS + BLS Employment, Building Permits |
| `ViolationNormalizer` | `transforms/normalize_violations.py` | DOB Violations, HPD Violations |
| `SalesNormalizer` | `transforms/normalize_sales.py` | NYC Rolling Sales |
| `NeighborhoodSignalNormalizer` | `transforms/normalize_neighborhood.py` | 311 Complaints |

Normalizers for transit access and fair market rent data are handled at ingestion time in the bronze-to-silver pipeline rather than through dedicated normalizer classes, since their schemas closely mirror the raw source format.

All normalizers with upsert logic match on BBL, parcel_id, address, or zip_code to prevent duplicate records.
