from __future__ import annotations

import os
from contextlib import asynccontextmanager
from collections.abc import AsyncIterator
from pathlib import Path

from dotenv import load_dotenv
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from backend.data_pipeline.silver.models.connection import DatabaseModel

_ENV_LOADED = False


def _ensure_env_loaded() -> None:
    global _ENV_LOADED
    if _ENV_LOADED:
        return
    backend_dir = Path(__file__).resolve().parents[1]
    env_path = backend_dir / ".env"
    if not env_path.exists():
        env_path = backend_dir / "data_pipeline" / ".env"
    if env_path.exists():
        load_dotenv(dotenv_path=env_path)
    _ENV_LOADED = True


def _get_postgres_dsn() -> str:
    _ensure_env_loaded()
    return os.getenv(
        "POSTGRES_DSN",
        "",
    )


class DatabaseProvider:
    """Sole owner of the database connection lifecycle.

    Provides a single session() context manager that yields an active
    AsyncSession. Callers use session.add(), session.execute(), etc.
    directly — no extra read/write wrappers.
    """

    def __init__(self, postgres_dsn: str | None = None) -> None:
        self._dsn = postgres_dsn or _get_postgres_dsn()
        self._engine: AsyncEngine | None = None

    @property
    def engine(self) -> AsyncEngine:
        if self._engine is None:
            self._engine = create_async_engine(
                self._dsn,
                pool_size=5,
                max_overflow=10,
                echo=False,
            )
        return self._engine

    @property
    def session_factory(self) -> async_sessionmaker[AsyncSession]:
        return async_sessionmaker(
            bind=self.engine,
            class_=AsyncSession,
            expire_on_commit=False,
        )

    @asynccontextmanager
    async def session(self) -> AsyncIterator[AsyncSession]:
        """Yield an active AsyncSession.

        The caller performs all operations (reads, writes, commits)
        directly on the session. Rolls back on unhandled exceptions.
        """
        active_session = self.session_factory()
        try:
            yield active_session
            await active_session.commit()
        except Exception:
            await active_session.rollback()
            raise
        finally:
            await active_session.close()

    async def initialize_tables(self) -> None:
        """Create all tables defined by DatabaseModel metadata."""
        async with self.engine.begin() as connection:
            await connection.run_sync(DatabaseModel.metadata.create_all)

    async def dispose(self) -> None:
        """Shut down the engine and release the connection pool."""
        if self._engine:
            await self._engine.dispose()
            self._engine = None
