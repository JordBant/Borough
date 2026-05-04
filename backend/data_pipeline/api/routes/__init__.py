from backend.data_pipeline.api.routes.property_routes import property_router
from backend.data_pipeline.api.routes.market_routes import market_router
from backend.data_pipeline.api.routes.forecast_routes import forecast_router
from backend.data_pipeline.api.routes.comps_routes import comps_router
from backend.data_pipeline.api.routes.alerts_routes import alerts_router
from backend.data_pipeline.api.routes.ingest_routes import ingest_router

__all__ = [
    "property_router",
    "market_router",
    "forecast_router",
    "comps_router",
    "alerts_router",
    "ingest_router",
]
