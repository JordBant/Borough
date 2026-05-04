from __future__ import annotations

import uuid
from datetime import date

from sqlalchemy import Date, DateTime, ForeignKey, Integer, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.sql import func

TIMESTAMPTZ = DateTime(timezone=True)

from backend.data_pipeline.silver.models.connection import DatabaseModel


class NeighborhoodSignalRecord(DatabaseModel):
    __tablename__ = "neighborhood_signals"

    signal_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    submarket_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("submarkets.submarket_id"),
        nullable=True,
    )
    zip_code: Mapped[str] = mapped_column(Text, nullable=False)
    complaint_type: Mapped[str] = mapped_column(Text, nullable=False)
    complaint_count: Mapped[int] = mapped_column(Integer, nullable=False)
    period_start: Mapped[date] = mapped_column(Date, nullable=False)
    period_end: Mapped[date] = mapped_column(Date, nullable=False)
    source: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[None] = mapped_column(
        TIMESTAMPTZ, server_default=func.now()
    )
