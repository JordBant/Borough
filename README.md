# Borough

Brooklyn rental market intelligence platform. Ingests property data, signed lease comps, economic indicators, and supply pipeline data from **free public sources only** to produce a per-property **Rent Pressure Score (RPS)** and probabilistic rent forecasts.

The core strategy is **"truth through overlap"** — instead of relying on any single paid data vendor, Borough combines 16 independent free data sources and assigns confidence scores based on source authority and agreement.

---

## Architecture

The backend follows a **medallion ETL pattern**:

```
Bronze (Raw Data Lake)  →  Silver (Normalized Postgres)  →  Gold (Feature Store)  →  API
```

| Layer | Purpose | Storage |
|---|---|---|
| **Bronze** | Immutable raw payloads from 16 free public sources | S3 / MinIO (JSON) |
| **Silver** | BBL-based entity-resolved records with UUID keys (11 tables) | PostgreSQL |
| **Gold** | Pre-computed features at property and submarket level (12 calculators) | PostgreSQL |

---

## Data Sources (All Free)

### NYC Open Data (Socrata API) — 10 sources

| Source | Data Provided |
|---|---|
| MapPLUTO | Property lot attributes, zoning, building class, square footage |
| DHCR Rent Stabilized | Rent-stabilized building records with legal regulated rents |
| DOB Job Filings | New building and alteration filings |
| DOB Violations | Building code violations with penalty amounts |
| HPD Violations | Housing maintenance violations (class A/B/C severity) |
| HPD Litigation | Housing court cases and case status |
| Building Permits | Issued construction permits |
| 421-a Filings | Tax abatement program filings and expiration dates |
| Rolling Sales | Annualized property sale records with prices |
| 311 Complaints | Noise, heat/hot water, plumbing, and building complaints |

### Federal APIs — 4 sources

| Source | Data Provided |
|---|---|
| Census ACS 5-year | Median income, population, renter occupancy, vacancy estimates |
| BLS Employment | Local area unemployment and employment trends |
| FRED Mortgage Rates | 30-year fixed mortgage rate time series |
| HUD Fair Market Rents | Official rent benchmarks by zip code and bedroom count |

### Transit and Trends — 2 sources

| Source | Data Provided |
|---|---|
| MTA Subway Ridership | Station-level daily ridership counts with lat/lng |
| Google Trends (pytrends) | Search interest signals for Brooklyn neighborhood demand |

---

## Source Confidence Scoring

Every data source has a confidence weight (0–100) defined in `config/constants.py`:

| Tier | Score | Sources |
|---|---|---|
| Highest (95) | Government records | PLUTO, DHCR, FRED |
| High (90) | Agency filings | DOB, HPD, Census, HUD, Building Permits, 421-a |
| Moderate (85) | Compiled data | Rolling Sales, BLS, MTA |
| Lower (80) | Complaint data | 311 Complaints |
| Lowest (50) | Search signals | Google Trends |

When multiple sources agree on a data point, composite confidence increases. This replaces the need for any paid authoritative source.

---

## Project Structure

```
Borough/
├── backend/
│   ├── config/                 # Environment settings, enums, constants
│   │   ├── settings.py         # Single point of truth for all env vars
│   │   └── constants.py        # DataSourceName, BrooklynSubmarket, confidence scores
│   ├── bronze/                 # Extraction layer (raw data lake)
│   │   ├── clients/            # Abstracted HTTP clients by source type
│   │   │   ├── base_client.py
│   │   │   ├── government_api_client.py  # NYC Open Data / MTA
│   │   │   ├── federal_api_client.py     # Census / BLS / FRED / HUD
│   │   │   └── web_scraper_client.py     # Playwright (available, not actively used)
│   │   ├── sources/            # One extractor per data source (16 total)
│   │   └── storage/            # S3/MinIO bronze object store
│   ├── silver/                 # Transformation layer (normalized Postgres)
│   │   ├── database/           # Async SQLAlchemy engine + session management
│   │   ├── schemas/            # One SQLAlchemy model per table (11 tables)
│   │   └── transforms/         # Normalizers mapping raw payloads to schema (7 normalizers)
│   ├── gold/                   # Loading layer (feature store)
│   │   ├── features/
│   │   │   ├── property_level/ # 6 per-property feature calculators
│   │   │   └── submarket_level/# 6 per-submarket feature calculators
│   │   └── store/              # Feature store writer / orchestrator
│   ├── api/                    # FastAPI route stubs (6 endpoints + health check)
│   │   └── routes/
│   ├── main.py                 # FastAPI application entry point
│   ├── requirements.txt
│   ├── .env.example
│   └── brooklyn_rental_pipeline_plan.md
├── infrastructure/             # Terraform IaC for AWS S3 bronze bucket
│   ├── main.tf
│   ├── variables.tf
│   └── outputs.tf
└── README.md
```

---

## Prerequisites

- **Python 3.11+**
- **PostgreSQL 15+** (running locally or via Docker)
- **MinIO** (for local S3-compatible bronze storage) or an AWS account
- **Redis** (for Celery task queue)

---

## Getting Started

### 1. Clone and enter the project

```bash
git clone <repo-url> Borough
cd Borough
```

### 2. Create and activate the virtual environment

```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Set up environment variables

```bash
cp .env.example .env
```

Edit `.env` and add your API keys. All keys are **free** and **optional** (they increase rate limits but are not required for basic access).

### 5. Start infrastructure services

```bash
# PostgreSQL
docker run -d --name borough-postgres \
  -e POSTGRES_USER=borough \
  -e POSTGRES_PASSWORD=borough \
  -e POSTGRES_DB=borough \
  -p 5432:5432 \
  postgres:15

# MinIO (S3-compatible bronze storage)
docker run -d --name borough-minio \
  -e MINIO_ROOT_USER=minioadmin \
  -e MINIO_ROOT_PASSWORD=minioadmin \
  -p 9000:9000 -p 9001:9001 \
  minio/minio server /data --console-address ":9001"

# Redis (Celery broker)
docker run -d --name borough-redis \
  -p 6379:6379 \
  redis:7
```

### 6. Run the API server

```bash
uvicorn backend.main:app --reload --host 0.0.0.0 --port 8000
```

The API will be available at `http://localhost:8000`. Visit `http://localhost:8000/docs` for the interactive Swagger UI.

---

## API Endpoints

| Method | Path | Description |
|---|---|---|
| `GET` | `/` | Health check |
| `GET` | `/property/{property_id}` | Property profile with RPS and source confidence |
| `GET` | `/market/{zip_code}` | Submarket metrics: vacancy, violations, transit, HUD FMR |
| `GET` | `/forecast/{property_id}` | 12-month probabilistic rent forecast with model inputs |
| `GET` | `/comps/{property_id}` | Comparable properties from DHCR leases and rolling sales |
| `GET` | `/alerts/high-pressure` | Properties with RPS >= 80 in last 30 days |
| `POST` | `/ingest/listing` | Manually push a listing into the pipeline |

---

## API Keys (All Free)

| Service | Env Variable | Registration URL |
|---|---|---|
| FRED | `FRED_API_KEY` | https://fred.stlouisfed.org/docs/api/api_key.html |
| Census Bureau | `CENSUS_API_KEY` | https://api.census.gov/data/key_signup.html |
| BLS | `BLS_API_KEY` | https://data.bls.gov/registrationEngine/ |
| NYC Open Data | `NYC_OPEN_DATA_APP_TOKEN` | https://data.cityofnewyork.us/profile/edit/developer_settings |

All keys are **optional** — APIs work without them but apply stricter rate limits. No paid services are required.

---

## Infrastructure (Terraform)

To provision the AWS S3 bronze bucket:

```bash
cd infrastructure
terraform init
terraform plan -var="environment=dev"
terraform apply -var="environment=dev"
```

---

## Frontend (React + Mapbox)

A 3D interactive map of Brooklyn rendered with Mapbox GL JS in dusk mode. Non-Brooklyn areas are masked with a dark overlay to focus attention on Brooklyn zip codes.

### Running the frontend

```bash
cd frontend
cp .env.example .env
```

Edit `.env` and add your Mapbox access token (free at [account.mapbox.com](https://account.mapbox.com/access-tokens/)).

```bash
yarn install
yarn dev
```

The app will be available at `http://localhost:5173`.

### Frontend structure

```
frontend/
├── src/
│   ├── components/
│   │   └── BrooklynMap/        # 3D dusk map with boundary mask
│   │       ├── BrooklynMap.jsx # Main map component
│   │       ├── BrooklynMap.css # Map and legend styles
│   │       ├── maskUtils.js    # Inverted polygon mask builder
│   │       └── index.js
│   ├── data/
│   │   ├── brooklynBoundary.js # Brooklyn GeoJSON boundary + zip codes
│   │   └── mockProperties.js   # Mock rental property data
│   ├── App.jsx
│   ├── main.jsx
│   └── index.css
├── .env.example
├── index.html
├── package.json
└── vite.config.js
```

---

## Current Status

**Phase 1 (Foundation):** Complete — 16 free-source extraction clients, bronze storage, 11 silver database schemas, 7 normalizers with BBL-based identity resolution.

**Phase 2 (Intelligence):** Complete — 12 feature calculators (6 property-level, 6 submarket-level), feature store orchestration, source confidence scoring.

**Phase 3 (Surface):** 3D Brooklyn map with dusk mode and boundary masking. Full backend integration pending.
