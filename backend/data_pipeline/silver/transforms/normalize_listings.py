from __future__ import annotations

from datetime import date

from sqlalchemy.ext.asyncio import AsyncSession

from backend.data_pipeline.silver.schemas.listings import ListingRecord


def _parse_date(value: str | None) -> date | None:
    if not value:
        return None
    return date.fromisoformat(value)


class ListingNormalizer:
    """Normalizes listing data into ListingRecord shape.

    Paid sources (StreetEasy, Zillow) have been removed. The listings table
    will be populated from broker feeds or approved APIs once available.
    """

    @staticmethod
    def normalize_from_manual_entry(raw_payload: dict) -> dict:
        return {
            "source": raw_payload.get("source", "manual_entry"),
            "asking_rent": raw_payload.get("asking_rent", 0),
            "list_date": _parse_date(raw_payload.get("list_date")),
            "removed_date": _parse_date(raw_payload.get("removed_date")),
            "days_on_market": raw_payload.get("days_on_market"),
        }

    @staticmethod
    async def persist_normalized_listing(
        session: AsyncSession, normalized_data: dict
    ) -> ListingRecord:
        new_record = ListingRecord(**normalized_data)
        session.add(new_record)
        return new_record
