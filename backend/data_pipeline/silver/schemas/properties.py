from __future__ import annotations

import uuid

from sqlalchemy import DateTime, ForeignKey, Integer, Numeric, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.sql import func

TIMESTAMPTZ = DateTime(timezone=True)

from backend.data_pipeline.silver.models.connection import DatabaseModel


class PropertyRecord(DatabaseModel):
    __tablename__ = "properties"

    property_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    address: Mapped[str] = mapped_column(Text, nullable=False)
    parcel_id: Mapped[str | None] = mapped_column(Text, nullable=True)
    latitude: Mapped[float | None] = mapped_column(
        Numeric(precision=10, scale=7), nullable=True
    )
    longitude: Mapped[float | None] = mapped_column(
        Numeric(precision=10, scale=7), nullable=True
    )
    bedrooms: Mapped[int | None] = mapped_column(Integer, nullable=True)
    bathrooms: Mapped[float | None] = mapped_column(
        Numeric(precision=3, scale=1), nullable=True
    )
    square_footage: Mapped[int | None] = mapped_column(Integer, nullable=True)
    year_built: Mapped[int | None] = mapped_column(Integer, nullable=True)
    submarket_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("submarkets.submarket_id"),
        nullable=True,
    )
    created_at: Mapped[None] = mapped_column(
        TIMESTAMPTZ, server_default=func.now()
    )
    updated_at: Mapped[None] = mapped_column(
        TIMESTAMPTZ, server_default=func.now(), onupdate=func.now()
    )
