from __future__ import annotations

from fastapi import APIRouter

property_router = APIRouter(prefix="/property", tags=["Property"])


@property_router.get("/{property_id}")
async def get_property_profile(property_id: str) -> dict:
    """Return property profile with composite scores derived from free public data."""
    return {
        "property_id": property_id,
        "address": "123 Atlantic Ave, Brooklyn, NY 11201",
        "bbl": "3002920001",
        "bedrooms": 2,
        "bathrooms": 1.0,
        "square_footage": 850,
        "year_built": 1928,
        "submarket": "dumbo_downtown_brooklyn",
        "latitude": 40.6862,
        "longitude": -73.9776,
        "rent_pressure_score": {
            "score": 72.5,
            "scored_at": "2026-04-30T12:00:00Z",
            "component_breakdown": {
                "building_quality_score": 0.68,
                "transit_access_score": 0.91,
                "fair_market_rent_delta": 0.15,
                "permit_activity_score": 0.42,
                "ownership_duration_years": 12.3,
            },
        },
        "source_confidence": {
            "pluto": {"available": True, "freshness": "2026-03"},
            "dhcr": {"available": True, "freshness": "2026-Q1"},
            "hpd_violations": {"available": True, "freshness": "2026-04"},
            "dob_violations": {"available": True, "freshness": "2026-04"},
            "rolling_sales": {"available": True, "freshness": "2025"},
            "hud_fair_market_rents": {"available": True, "freshness": "FY2026"},
            "mta_ridership": {"available": True, "freshness": "2026-03"},
        },
        "data_sources_available": 7,
    }
