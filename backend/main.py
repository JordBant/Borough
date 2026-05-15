from __future__ import annotations

import logging
from contextlib import asynccontextmanager
from collections.abc import AsyncIterator

from fastapi import FastAPI

from backend.data_pipeline.api.routes._dev_source_test_routes import (
    dev_source_test_router,
)
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

# Temporary: per-source smoke-test endpoints; remove this include alongside the file.
app.include_router(dev_source_test_router)


@app.get("/")
async def health_check() -> dict:
    return {"status": "healthy", "service": "borough"}
