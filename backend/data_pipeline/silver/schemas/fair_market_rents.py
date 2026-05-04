from __future__ import annotations

import uuid

from sqlalchemy import DateTime, Integer, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.sql import func

TIMESTAMPTZ = DateTime(timezone=True)

from backend.data_pipeline.silver.models.connection import DatabaseModel


class FairMarketRentRecord(DatabaseModel):
    __tablename__ = "fair_market_rents"

    record_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    zip_code: Mapped[str] = mapped_column(Text, nullable=False)
    year: Mapped[int] = mapped_column(Integer, nullable=False)
    efficiency_rent: Mapped[int] = mapped_column(Integer, nullable=False)
    one_bedroom_rent: Mapped[int] = mapped_column(Integer, nullable=False)
    two_bedroom_rent: Mapped[int] = mapped_column(Integer, nullable=False)
    three_bedroom_rent: Mapped[int] = mapped_column(Integer, nullable=False)
    four_bedroom_rent: Mapped[int] = mapped_column(Integer, nullable=False)
    created_at: Mapped[None] = mapped_column(
        TIMESTAMPTZ, server_default=func.now()
    )
