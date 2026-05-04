from __future__ import annotations

import abc
import logging

from playwright.async_api import async_playwright

from backend.data_pipeline.config.settings import EnvironmentSettings
from backend.data_pipeline.config.constants import DataSourceName
from backend.data_pipeline.bronze.clients.base_client import BaseExtractionClient

logger = logging.getLogger(__name__)

_DEFAULT_NAVIGATION_TIMEOUT_MS = 60_000


class WebScraperClient(BaseExtractionClient, abc.ABC):
    """Extraction client for JavaScript-heavy pages that require a real browser."""

    def __init__(
        self,
        settings: EnvironmentSettings,
        source_name: DataSourceName,
    ) -> None:
        super().__init__(settings, source_name)

    async def execute_scrape(
        self,
        url: str,
        wait_for_selector: str | None = None,
    ) -> str:
        """Launch a headless browser, navigate to *url*, and return page HTML."""
        async with async_playwright() as playwright_instance:
            browser = await playwright_instance.chromium.launch(headless=True)
            page = await browser.new_page()
            try:
                await page.goto(url, timeout=_DEFAULT_NAVIGATION_TIMEOUT_MS)
                if wait_for_selector:
                    await page.wait_for_selector(
                        wait_for_selector,
                        timeout=_DEFAULT_NAVIGATION_TIMEOUT_MS,
                    )
                html_content = await page.content()
            finally:
                await browser.close()
        return html_content

    @abc.abstractmethod
    def parse_html(self, raw_html: str) -> dict:
        """Parse scraped HTML into a structured dict. Source-specific."""

    async def extract_raw_data(self, **kwargs: object) -> dict:
        """Orchestrate scrape then parse."""
        url = str(kwargs["url"])
        wait_for_selector = kwargs.get("wait_for_selector")
        selector_value = str(wait_for_selector) if wait_for_selector else None
        raw_html = await self.execute_scrape(url, wait_for_selector=selector_value)
        return self.parse_html(raw_html)
