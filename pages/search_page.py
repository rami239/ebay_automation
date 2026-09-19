import logging
from typing import List
from urllib.parse import urljoin

from playwright.sync_api import Page, expect

from pages.base_page import BasePage
from utils.price_parser import parse_price


logger = logging.getLogger(__name__)


class SearchPage(BasePage):
    def __init__(self, page: Page):
        super().__init__(page)

        # The exercise explicitly asks to extract matching products using XPath.
        self.product_items = (
            "xpath=//ul[contains(@class,'srp-results')]"
            "//li[contains(@class,'s-item')]"
        )
        self.search_input = "#searchInput"
        self.search_button = "#searchBtn"
        self.next_button = "#nextBtn"
        self.page_number = "#pageNumber"
        self.results_container = "#results"
        self.last_matches: list[dict] = []

    def navigate(self, base_url: str) -> None:
        self.page.goto(f"{base_url}/mock_ebay.html", wait_until="domcontentloaded")
        expect(self.page.locator(self.search_input)).to_be_visible(timeout=5000)

    def search_items_by_name_under_price(
        self,
        query: str,
        max_price: float,
        limit: int = 5,
    ) -> List[str]:
        """Return up to `limit` product URLs whose displayed price is <= max_price."""
        if not query or not query.strip():
            raise ValueError("query must not be empty.")
        if max_price < 0:
            raise ValueError("max_price must be greater than or equal to 0.")
        if limit <= 0:
            self.last_matches = []
            return []

        self.last_matches = []
        self.page.locator(self.search_input).fill(query)
        self.page.locator(self.search_button).click()
        expect(self.page.locator(self.results_container)).to_be_visible(timeout=5000)

        valid_urls: List[str] = []
        seen_urls: set[str] = set()

        while len(valid_urls) < limit:
            items = self.page.locator(self.product_items)
            item_count = items.count()
            logger.info("Scanning results page; cards detected: %s", item_count)

            for index in range(item_count):
                if len(valid_urls) >= limit:
                    break

                item = items.nth(index)
                price_locator = item.locator(
                    "xpath=.//span[contains(@class,'s-item__price')]"
                )
                link_locator = item.locator(
                    "xpath=.//a[contains(@class,'s-item__link')]"
                )

                if price_locator.count() == 0 or link_locator.count() == 0:
                    logger.warning("Skipping malformed product card #%s", index + 1)
                    continue

                price_text = price_locator.first.inner_text().strip()
                try:
                    price = parse_price(price_text)
                except ValueError:
                    logger.warning("Could not parse product price: %s", price_text)
                    continue

                href = link_locator.first.get_attribute("href")
                name = link_locator.first.inner_text().strip()
                if not href or price > max_price:
                    continue

                absolute_url = urljoin(self.page.url, href)
                if absolute_url in seen_urls:
                    continue

                valid_urls.append(absolute_url)
                seen_urls.add(absolute_url)
                self.last_matches.append(
                    {"name": name, "price": price, "url": absolute_url}
                )
                logger.info("MATCH: %s | $%.2f | %s", name, price, absolute_url)

            if len(valid_urls) >= limit:
                break

            next_button = self.page.locator(self.next_button)
            if (
                next_button.count() == 0
                or not next_button.is_visible()
                or next_button.is_disabled()
            ):
                break

            current_page = self.page.locator(self.page_number).inner_text().strip()
            next_button.click()
            expect(self.page.locator(self.page_number)).not_to_have_text(
                current_page,
                timeout=5000,
            )

        self.take_screenshot("Search_Results")
        logger.info("Search complete; valid URLs collected: %s", len(valid_urls))
        return valid_urls
