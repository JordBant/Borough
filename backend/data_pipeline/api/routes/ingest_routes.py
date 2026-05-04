from __future__ import annotations

from fastapi import APIRouter
from pydantic import BaseModel


class ManualListingPayload(BaseModel):
    address: str
    asking_rent: int
    bedrooms: int
    bathrooms: float
    source: str = "manual"


ingest_router = APIRouter(prefix="/ingest", tags=["Ingest"])


@ingest_router.post("/listing")
async def ingest_manual_listing(payload: ManualListingPayload) -> dict:
    """Manually push a new listing into the pipeline."""
    return {
        "status": "accepted",
        "message": f"Listing for {payload.address} queued for ingestion.",
        "listing_id": "placeholder-uuid-will-be-generated",
    }
