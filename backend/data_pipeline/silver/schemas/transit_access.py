from __future__ import annotations

import uuid
from datetime import date

from sqlalchemy import Date, DateTime, Integer, Numeric, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.sql import func

TIMESTAMPTZ = DateTime(timezone=True)

from backend.data_pipeline.silver.models.connection import DatabaseModel


class TransitAccessRecord(DatabaseModel):
    __tablename__ = "transit_access"

    station_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    station_name: Mapped[str] = mapped_column(Text, nullable=False)
    station_complex_id: Mapped[str | None] = mapped_column(Text, nullable=True)
    latitude: Mapped[float] = mapped_column(
        Numeric(precision=10, scale=7), nullable=False
    )
    longitude: Mapped[float] = mapped_column(
        Numeric(precision=10, scale=7), nullable=False
    )
    average_daily_ridership: Mapped[int | None] = mapped_column(
        Integer, nullable=True
    )
    measurement_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    created_at: Mapped[None] = mapped_column(
        TIMESTAMPTZ, server_default=func.now()
    )
