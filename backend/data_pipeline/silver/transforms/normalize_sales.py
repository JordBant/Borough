from __future__ import annotations

from datetime import date

from sqlalchemy.ext.asyncio import AsyncSession

from backend.data_pipeline.config.constants import DataSourceName
from backend.data_pipeline.silver.schemas.property_sales import PropertySaleRecord


def _parse_date(value: str | None) -> date | None:
    if not value:
        return None
    return date.fromisoformat(value)


class SalesNormalizer:
    """Normalizes raw property sales data from NYC rolling sales into PropertySaleRecord shape."""

    @staticmethod
    def normalize_from_rolling_sales(raw_payload: dict) -> dict:
        borough = raw_payload.get("borough", "")
        block = raw_payload.get("block", "")
        lot = raw_payload.get("lot", "")
        borough_block_lot = f"{borough}-{block}-{lot}"
        return {
            "borough_block_lot": borough_block_lot,
            "address": raw_payload.get("address", ""),
            "building_class": raw_payload.get("building_class", ""),
            "sale_price": raw_payload.get("sale_price", 0),
            "sale_date": _parse_date(raw_payload.get("sale_date")),
            "residential_units": raw_payload.get("residential_units"),
            "year_built": raw_payload.get("year_built"),
        }

    @staticmethod
    async def persist_normalized_sale(
        session: AsyncSession, normalized_data: dict
    ) -> PropertySaleRecord:
        new_record = PropertySaleRecord(**normalized_data)
        session.add(new_record)
        return new_record
