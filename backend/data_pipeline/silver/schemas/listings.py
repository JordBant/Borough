from __future__ import annotations

import uuid
from datetime import date

from sqlalchemy import Date, DateTime, ForeignKey, Integer, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.sql import func

TIMESTAMPTZ = DateTime(timezone=True)

from backend.data_pipeline.silver.models.connection import DatabaseModel


class ListingRecord(DatabaseModel):
    __tablename__ = "listings"

    listing_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    property_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("properties.property_id"),
        nullable=False,
    )
    source: Mapped[str] = mapped_column(Text, nullable=False)
    asking_rent: Mapped[int] = mapped_column(Integer, nullable=False)
    list_date: Mapped[date] = mapped_column(Date, nullable=False)
    removed_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    days_on_market: Mapped[int | None] = mapped_column(Integer, nullable=True)
    created_at: Mapped[None] = mapped_column(
        TIMESTAMPTZ, server_default=func.now()
    )
