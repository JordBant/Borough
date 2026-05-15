from __future__ import annotations

from datetime import datetime, timezone

from backend.data_pipeline.config.settings import EnvironmentSettings
from backend.data_pipeline.config.constants import DataSourceName
from backend.data_pipeline.bronze.clients.base_client import BaseExtractionClient

BASE_URL_TEMPLATE = "https://www.huduser.gov/hudapi/public/fmr/data/{entity_id}"

NYC_METRO_ENTITY_ID = "METRO35620M35620"


class HudFairMarketRentsExtractor(BaseExtractionClient):
    """Extract HUD Fair Market Rent data for the NYC metro area."""

    def __init__(self, settings: EnvironmentSettings) -> None:
        super().__init__(settings, DataSourceName.HUD_FAIR_MARKET_RENTS)

    async def extract_raw_data(self, **kwargs: object) -> dict:
        entity_id = str(kwargs.get("entity_id", NYC_METRO_ENTITY_ID))
        year = str(
            kwargs.get("year", datetime.now(timezone.utc).year)
        )

        url = BASE_URL_TEMPLATE.format(entity_id=entity_id)

        query_parameters: dict[str, str] = {"year": year}

        response_data = await self.execute_get_request(
            url,
            query_parameters=query_parameters,
        )
        return {"entity_id": entity_id, "year": year, "data": response_data}
