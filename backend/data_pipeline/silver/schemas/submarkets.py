from __future__ import annotations

import uuid

from sqlalchemy import DateTime, Numeric, Text, Integer
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.sql import func

TIMESTAMPTZ = DateTime(timezone=True)

from backend.data_pipeline.silver.models.connection import DatabaseModel


class SubmarketRecord(DatabaseModel):
    __tablename__ = "submarkets"

    submarket_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    zip_code: Mapped[str] = mapped_column(Text, nullable=False)
    neighborhood: Mapped[str] = mapped_column(Text, nullable=False)
    vacancy_rate: Mapped[float | None] = mapped_column(Numeric, nullable=True)
    job_growth_rate: Mapped[float | None] = mapped_column(Numeric, nullable=True)
    supply_pipeline_units: Mapped[int | None] = mapped_column(Integer, nullable=True)
    updated_at: Mapped[None] = mapped_column(
        TIMESTAMPTZ, server_default=func.now(), onupdate=func.now()
    )
