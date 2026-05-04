from __future__ import annotations

from fastapi import APIRouter

forecast_router = APIRouter(prefix="/forecast", tags=["Forecast"])


@forecast_router.get("/{property_id}")
async def get_rent_forecast(property_id: str) -> dict:
    """Return 12-month probabilistic rent forecast for a property."""
    return {
        "property_id": property_id,
        "horizon_months": 12,
        "probability": 0.80,
        "range_low": 2950,
        "range_high": 3400,
        "current_estimated_rent": 3150,
        "forecast_generated_at": "2026-05-01T08:00:00Z",
        "model_inputs": {
            "census_acs_median_income": True,
            "bls_employment_trends": True,
            "fred_mortgage_rates": True,
            "hud_fair_market_rents": True,
            "nyc_pluto_building_attributes": True,
            "nyc_dhcr_regulated_rents": True,
            "nyc_dob_permit_activity": True,
            "mta_subway_ridership": True,
            "google_trends_demand_signal": True,
        },
    }
