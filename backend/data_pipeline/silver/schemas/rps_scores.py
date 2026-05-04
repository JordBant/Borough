from __future__ import annotations

import uuid

from sqlalchemy import DateTime, ForeignKey, Numeric
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.sql import func

TIMESTAMPTZ = DateTime(timezone=True)

from backend.data_pipeline.silver.models.connection import DatabaseModel


class RentPressureScoreRecord(DatabaseModel):
    __tablename__ = "rps_scores"

    score_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    property_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("properties.property_id"),
        nullable=False,
    )
    scored_at: Mapped[None] = mapped_column(TIMESTAMPTZ, nullable=False)
    rent_pressure_score: Mapped[float] = mapped_column(Numeric, nullable=False)
    component_breakdown: Mapped[dict] = mapped_column(JSONB, nullable=False)
    created_at: Mapped[None] = mapped_column(
        TIMESTAMPTZ, server_default=func.now()
    )
