from __future__ import annotations

import uuid
from datetime import date

from sqlalchemy import Date, DateTime, ForeignKey, Numeric, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.sql import func

TIMESTAMPTZ = DateTime(timezone=True)

from backend.data_pipeline.silver.models.connection import DatabaseModel


class BuildingViolationRecord(DatabaseModel):
    __tablename__ = "building_violations"

    violation_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    property_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("properties.property_id"),
        nullable=True,
    )
    source: Mapped[str] = mapped_column(Text, nullable=False)
    violation_class: Mapped[str] = mapped_column(Text, nullable=False)
    violation_date: Mapped[date] = mapped_column(Date, nullable=False)
    disposition_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    penalty_amount: Mapped[float | None] = mapped_column(Numeric, nullable=True)
    status: Mapped[str] = mapped_column(Text, nullable=False)
    borough_block_lot: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[None] = mapped_column(
        TIMESTAMPTZ, server_default=func.now()
    )
