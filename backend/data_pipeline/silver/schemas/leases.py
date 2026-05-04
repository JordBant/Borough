from __future__ import annotations

import uuid
from datetime import date

from sqlalchemy import Date, DateTime, ForeignKey, Integer, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.sql import func

TIMESTAMPTZ = DateTime(timezone=True)

from backend.data_pipeline.silver.models.connection import DatabaseModel


class LeaseRecord(DatabaseModel):
    __tablename__ = "leases"

    lease_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    property_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("properties.property_id"),
        nullable=False,
    )
    signed_rent: Mapped[int] = mapped_column(Integer, nullable=False)
    lease_start_date: Mapped[date] = mapped_column(Date, nullable=False)
    lease_end_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    concessions: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[None] = mapped_column(
        TIMESTAMPTZ, server_default=func.now()
    )
