from __future__ import annotations

from pytrends.request import TrendReq

from backend.data_pipeline.config.settings import EnvironmentSettings
from backend.data_pipeline.config.constants import DataSourceName
from backend.data_pipeline.bronze.clients.base_client import BaseExtractionClient

DEFAULT_GEO_CODE = "US-NY"
DEFAULT_TIMEFRAME = "today 12-m"
DEFAULT_KEYWORDS = [
    "brooklyn rent",
    "apartment brooklyn",
    "moving to brooklyn",
]


class GoogleTrendsExtractor(BaseExtractionClient):
    """Extract Google Trends interest-over-time data via the pytrends library."""

    def __init__(self, settings: EnvironmentSettings) -> None:
        super().__init__(settings, DataSourceName.GOOGLE_TRENDS)

    async def extract_raw_data(self, **kwargs: object) -> dict:
        keywords = kwargs.get("keywords") or DEFAULT_KEYWORDS
        geo_code = str(kwargs.get("geo_code", DEFAULT_GEO_CODE))
        timeframe = str(kwargs.get("timeframe", DEFAULT_TIMEFRAME))

        keyword_list: list[str] = list(keywords)  # type: ignore[arg-type]

        pytrends_client = TrendReq(hl="en-US", tz=300)
        pytrends_client.build_payload(
            keyword_list,
            cat=0,
            timeframe=timeframe,
            geo=geo_code,
        )

        interest_over_time_dataframe = pytrends_client.interest_over_time()

        records: list[dict] = []
        if not interest_over_time_dataframe.empty:
            interest_over_time_dataframe = interest_over_time_dataframe.drop(
                columns=["isPartial"], errors="ignore"
            )
            records = interest_over_time_dataframe.reset_index().to_dict(orient="records")
            for record in records:
                if "date" in record:
                    record["date"] = str(record["date"])

        return {
            "geo_code": geo_code,
            "timeframe": timeframe,
            "keywords": keyword_list,
            "records": records,
        }
