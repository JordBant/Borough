from __future__ import annotations

from sqlalchemy.orm import DeclarativeBase


class DatabaseModel(DeclarativeBase):
    """Declarative base inherited by every Silver schema model."""
