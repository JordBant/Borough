from __future__ import annotations

import logging
from contextlib import asynccontextmanager
from collections.abc import AsyncIterator

from fastapi import FastAPI

from backend.db.connection import DatabaseProvider

logger = logging.getLogger("borough")


@asynccontextmanager
async def application_lifespan(application: FastAPI) -> AsyncIterator[None]:
    database_provider = DatabaseProvider()
    await database_provider.initialize_tables()
    logger.info("Database tables initialized — Borough is ready.")
    application.state.database_provider = database_provider
    yield
    await database_provider.dispose()


app = FastAPI(
    title="Borough — Brooklyn Rental Market Intelligence",
    lifespan=application_lifespan,
)


@app.get("/")
async def health_check() -> dict:
    return {"status": "healthy", "service": "borough"}
