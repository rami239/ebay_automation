import logging
import random
from typing import Sequence

from playwright.sync_api import Locator, Page, expect

from pages.base_page import BasePage


logger = logging.getLogger(__name__)


class ProductPage(BasePage):
    def __init__(self, page: Page):
        super().__init__(page)
        self.variant_selects = "select[id^='variant-']"
        self.add_to_cart_button = "#addToCartBtn"
        self.back_to_search_button = "#backToSearchBtn"
        self.cart_count = "#cartCount"
        self.search_input = "#searchInput"
        self.product_title = "h1"

    @staticmethod
    def _select_random_available_option(select: Locator) -> str:
        options = select.locator("option:not([disabled])")
        values: list[str] = []

        for index in range(options.count()):
            value = options.nth(index).get_attribute("value")
            if value:
                values.append(value)

        if not values:
            raise AssertionError("Variant selector exists but has no available options.")

        selected_value = random.choice(values)
        select.select_option(value=selected_value)
        return selected_value

    def _select_available_variants(self) -> dict[str, str]:
        variants = self.page.locator(self.variant_selects)
        selected: dict[str, str] = {}

        for index in range(variants.count()):
            select = variants.nth(index)
            selector_id = select.get_attribute("id") or f"variant-{index + 1}"
            variant_name = selector_id.removeprefix("variant-").capitalize()
            selected_value = self._select_random_available_option(select)
            selected[variant_name] = selected_value
            logger.info("Selected %s: %s", variant_name, selected_value)

        return selected

    def add_items_to_cart(self, urls: Sequence[str]) -> list[dict]:
        added_products: list[dict] = []

        for index, url in enumerate(urls, start=1):
            logger.info("Adding product #%s: %s", index, url)

            try:
                self.page.goto(url, wait_until="domcontentloaded")
                expect(self.page.locator(self.add_to_cart_button)).to_be_visible(timeout=5000)

                product_name = self.page.locator(self.product_title).inner_text().strip()
                selected_variants = self._select_available_variants()

                cart_count = self.page.locator(self.cart_count)
                before_count = int(cart_count.inner_text().strip())

                self.page.locator(self.add_to_cart_button).click()
                expect(cart_count).to_have_text(str(before_count + 1), timeout=5000)

                after_count = before_count + 1
                logger.info(
                    "Product added successfully: %s | cart count=%s",
                    product_name,
                    after_count,
                )

                self.take_screenshot(f"Added_To_Cart_Product_{index}")

                added_products.append(
                    {
                        "url": url,
                        "name": product_name,
                        "variants": selected_variants,
                        "cart_count": after_count,
                    }
                )

                self.page.locator(self.back_to_search_button).click()
                expect(self.page.locator(self.search_input)).to_be_visible(timeout=5000)

            except Exception:
                self.take_screenshot(f"FAILED_Add_To_Cart_Product_{index}")
                raise

        return added_products
