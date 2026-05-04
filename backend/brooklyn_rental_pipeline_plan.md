# Brooklyn Rental Market Pipeline — Implementation Plan

## Overview

A property-level rent pressure engine scoped to Brooklyn, NY, built on the architecture:

```
Ingest → Normalize → Enrich → Feature Engineering → Score (RPS) → Forecast → API / UI
```

**Target submarkets:** Park Slope, Crown Heights, Bushwick, Williamsburg, Bay Ridge, Flatbush, DUMBO/Downtown Brooklyn.

---

## Phase 1 — Foundation

### Data Sources & Ingestion

#### Property-Level Sources

| Source | Data Collected |
|---|---|
| StreetEasy (scraper or RapidAPI) | Address, beds/baths, sqft, asking rent, list date, DOM, removed date |
| Zillow ZWSAPI | Asking rent, listing history, vacancy signals |
| Rentometer | Comp rent ranges by zip |
| NYC DHCR rent-stabilized records | **Signed lease comps** — strongest signal, actual effective rents |
| NYC MapPluto / DOF | Parcel ID, ownership history, lot size, year built |

#### Market-Level Sources

| Source | Data Collected |
|---|---|
| Census ACS 5yr | Migration, median income, household formation |
| BLS Local Area Unemployment | Employment growth, wage trends |
| NYC Open Data — building permits | Multifamily starts, supply pipeline |
| NYC Open Data — 421-a filings | Tax incentive expiry (signals rent trajectory shifts) |
| FRED API | Mortgage rates (30yr fixed, weekly) |
| Google Trends | Search demand by Brooklyn zip code |

#### Ingestion Stack

- **Runtime:** Python 3.11
- **API framework:** FastAPI
- **Task queue:** Celery + Redis
- **Orchestration:** Prefect (nightly DAG)
- **Async HTTP:** httpx
- **JS-heavy scraping:** Playwright
- **ETL processing:** Polars (preferred at scale), Pandas for prototyping

---

### Storage — Bronze → Silver → Gold

#### Bronze Layer (Raw Data Lake)

Never mutate. Store untouched source payloads for full replay and audit.

- **Store:** S3-compatible object storage (MinIO self-hosted or Cloudflare R2)
- **Format:** JSON blobs

```json
{
  "source": "streeteasy",
  "fetched_at": "2025-01-15T08:00:00Z",
  "payload": { ... }
}
```

#### Silver Layer (Normalized Postgres)

Entity-resolved canonical records. UUID `property_id` as primary key across all tables.

**Core tables:**

```sql
-- properties
property_id      UUID PRIMARY KEY
address          TEXT
parcel_id        TEXT
lat              DECIMAL
lng              DECIMAL
beds             INT
baths            DECIMAL
sqft             INT
year_built       INT
submarket_id     UUID REFERENCES submarkets

-- listings
listing_id       UUID PRIMARY KEY
property_id      UUID REFERENCES properties
source           TEXT
ask_rent         INT
list_date        DATE
removed_date     DATE
dom              INT

-- leases
lease_id         UUID PRIMARY KEY
property_id      UUID REFERENCES properties
signed_rent      INT
lease_start      DATE
lease_end        DATE
concessions      TEXT

-- submarkets
submarket_id     UUID PRIMARY KEY
zip_code         TEXT
neighborhood     TEXT
vacancy_rate     DECIMAL
job_growth       DECIMAL
supply_pipeline  INT
updated_at       TIMESTAMPTZ

-- rps_scores
score_id         UUID PRIMARY KEY
property_id      UUID REFERENCES properties
scored_at        TIMESTAMPTZ
rps              DECIMAL
component_json   JSONB
```

#### Gold Layer (Feature Store)

Pre-computed feature tables consumed by the scoring engine. Refreshed on each ingest cycle. Includes RPS inputs at both property and submarket level.

---

### Entity Resolution

Address normalization is the hardest part of the pipeline. A single Brooklyn property may appear across sources as:
- `123 Atlantic Ave`
- `123 Atlantic Avenue Apt 2`
- `123 ATLANTIC AVE #2`

**Resolution pipeline:**
1. Normalize via **SmartyStreets** (standardize address format)
2. Match on **NYC MapPluto parcel ID** (definitive dedup)
3. Geocode remaining unmatched addresses
4. Fuzzy match as last resort (Levenshtein distance on normalized strings)

---

## Phase 2 — Intelligence

### Feature Engineering

#### Property-Level Features

| Feature | Description |
|---|---|
| `rent_per_sqft` | Signed rent / sqft |
| `comp_adjusted_delta` | Asking rent vs nearby signed lease comps |
| `renovation_recency_score` | Proxy from permit pull history |
| `ownership_duration` | Years since last deed transfer |
| `turnover_likelihood` | Rolling DOM + lease length patterns |
| `concession_frequency` | % of listings offering free months in trailing 90 days |

#### Submarket-Level Features

| Feature | Description |
|---|---|
| `vacancy_compression` | Local vacancy vs Brooklyn borough average |
| `rent_growth_momentum` | 3, 6, 12-month signed rent growth rate |
| `mortgage_spillover_index` | Correlation of rate hikes to renter demand uptick |
| `affordability_ratio` | Median rent / median household income |
| `employer_dependency_risk` | Top-3 employer concentration in submarket |
| `supply_constraint_score` | Permitted units vs absorption rate |

---

### Rent Pressure Score (RPS)

The core product output. A single 0–100 score per property.

```
RPS = (0.30 × vacancy_compression)
    + (0.20 × lease_growth_momentum)
    + (0.15 × dom_compression)
    + (0.15 × mortgage_spillover)
    + (0.10 × supply_constraint)
    + (0.10 × employment_growth)
```

#### Interpretation

| Score | Signal |
|---|---|
| 80 – 100 | Aggressive upward pressure |
| 60 – 79 | Moderate growth |
| 40 – 59 | Stable |
| < 40 | Weakening / tenant-favored |

---

### Forecasting Layer

Always output probabilistic ranges — never a single deterministic number.

**Example output:**
> *74% probability rents rise 4–6% over 12 months. Expected range: $3,150–$3,350.*

#### MVP Model (Weeks 9–10)

- **Algorithm:** Ridge regression on RPS component features + seasonal dummies
- **Output:** Expected rent range + directional probability band
- **Why:** Fast to train, interpretable, debuggable — sufficient to validate product value

#### V2 Model (post-MVP, once 6+ months of labeled data exist)

- **Algorithm:** XGBoost or LightGBM
- **Why:** Captures non-linear interactions (e.g. high vacancy + constrained supply pipeline behaves differently than either signal alone)

> **Note:** Do not start with deep learning. It is almost always a mistake at this data scale and adds unnecessary complexity before product-market fit is established.

#### Seasonal Adjustment

Always normalize for Brooklyn's seasonal leasing cycle before computing trend signals:
- **Summer spike** (June–August): normalize upward DOM compression
- **Winter slowdown** (November–February): normalize downward leasing velocity

---

## Phase 3 — Surface

### API Layer (FastAPI)

```
GET  /property/{property_id}      — Canonical property profile + latest RPS
GET  /market/{zip_code}           — Submarket vacancy, DOM trends, supply pipeline
GET  /forecast/{property_id}      — 12-month probabilistic rent forecast
GET  /comps/{property_id}         — Comparable signed leases within radius
GET  /alerts/high-pressure        — Properties with RPS ≥ 80 in the last 30 days
POST /ingest/listing              — Manually push a new listing into the pipeline
```

---

### Frontend Dashboard (React)

| View | Description |
|---|---|
| Property lookup | Search by address, view RPS + forecast |
| Submarket heatmap | Brooklyn choropleth by RPS or vacancy rate |
| Comparable analysis | Signed lease comps within configurable radius |
| Rent forecast card | Probabilistic range, 3/6/12-month view |
| RPS leaderboard | Highest-pressure properties in trailing 30 days |
| Landlord pricing dashboard | Portfolio-level pricing power summary |

---

## Build Timeline — 12 Weeks

### Weeks 1–2 — Data Plumbing
Set up Postgres schema, S3 bronze layer, Celery workers. Wire first 3 sources: StreetEasy, NYC Open Data building permits, FRED mortgage rates. Validate that raw payloads land cleanly in the bronze layer.

### Weeks 3–4 — Entity Resolution
Build address normalization pipeline via SmartyStreets. Implement parcel ID matching against NYC MapPluto. Populate canonical `properties` table. Deduplicate across all active sources.

### Weeks 5–6 — Submarket Profiles
Ingest Census ACS, BLS local unemployment, and DHCR rent-stabilized records. Compute vacancy rate, DOM averages, and absorption rate per Brooklyn zip. Populate `submarkets` table with first full pass.

### Weeks 7–8 — RPS Engine
Build feature engineering layer. Implement weighted RPS formula. Store scores in `rps_scores` table. Run backtests against 12 months of historical Brooklyn listing data to validate signal quality.

### Weeks 9–10 — Forecasting + API
Train ridge regression model on RPS features. Add seasonal adjustment normalization. Expose all FastAPI endpoints. Internal QA pass on data quality and forecast plausibility.

### Weeks 11–12 — Dashboard MVP
Build React frontend: property lookup, submarket heatmap, RPS card. Deploy on Railway or Render. Set up nightly Prefect DAG for full pipeline refresh. Smoke test end-to-end flow.

---

## Strategic Principles

- **Local dominance over national mediocrity.** Dominate Brooklyn before expanding to other boroughs.
- **Signed lease comps are the strongest signal.** Prioritize DHCR data over asking rent indexes.
- **Probabilistic forecasting.** "83% probability rents rise 4–6%" is more defensible and useful than "rents will rise 7%."
- **Entity resolution is load-bearing.** The entire system is only as good as your property dedup. Invest here early.
- **Avoid deep learning until you have data.** XGBoost with clean features will outperform a neural network trained on 6 months of data.

---

## Next Steps

Once the MVP is stable, the natural expansion sequence is:

1. Add remaining Brooklyn zip codes and validate submarket boundaries
2. Integrate investor-facing signals (cap rate compression, institutional acquisition activity)
3. Expand to Queens and The Bronx using the same pipeline with new submarket configs
4. Upgrade forecasting model to LightGBM once 12+ months of labeled outcomes exist
5. Add webhook alerts for landlords when a property's RPS crosses a threshold
