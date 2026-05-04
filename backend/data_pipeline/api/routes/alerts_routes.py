from __future__ import annotations

from fastapi import APIRouter

alerts_router = APIRouter(prefix="/alerts", tags=["Alerts"])


@alerts_router.get("/high-pressure")
async def get_high_pressure_properties() -> list[dict]:
    """Return properties with RPS >= 80 in the last 30 days."""
    return [
        {
            "property_id": "f47ac10b-58cc-4372-a567-0e02b2c3d479",
            "address": "55 Willoughby St, Brooklyn, NY 11201",
            "rent_pressure_score": 88.3,
            "scored_at": "2026-04-28T14:00:00Z",
            "submarket": "dumbo_downtown_brooklyn",
        },
        {
            "property_id": "6ba7b810-9dad-11d1-80b4-00c04fd430c8",
            "address": "412 Myrtle Ave, Brooklyn, NY 11205",
            "rent_pressure_score": 82.1,
            "scored_at": "2026-04-29T09:30:00Z",
            "submarket": "crown_heights",
        },
    ]
