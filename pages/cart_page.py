import logging

from playwright.sync_api import Page, expect

from pages.base_page import BasePage
from utils.price_parser import parse_price


logger = logging.getLogger(__name__)


class CartPage(BasePage):
    def __init__(self, page: Page):
        super().__init__(page)
        self.open_cart_button = "#openCartBtn"
        self.cart_total = "#cartTotal"
        self.cart_items = ".cart-item"

    def assert_cart_total_not_exceeds(
        self,
        budget_per_item: float,
        items_count: int,
    ) -> float:
        if budget_per_item < 0:
            raise ValueError("budget_per_item must be greater than or equal to 0.")
        if items_count < 0:
            raise ValueError("items_count must be greater than or equal to 0.")

        # Open the cart through the UI, as an end user would.
        open_cart = self.page.locator(self.open_cart_button)
        expect(open_cart).to_be_visible(timeout=5000)
        open_cart.click()

        total_locator = self.page.locator(self.cart_total)
        expect(total_locator).to_be_visible(timeout=5000)

        actual_total = parse_price(total_locator.inner_text().strip())
        actual_items_count = self.page.locator(self.cart_items).count()
        max_allowed_budget = budget_per_item * items_count

        self.take_screenshot("Final_Cart_Review")

        assert actual_items_count == items_count, (
            f"Cart item count mismatch: expected {items_count}, "
            f"but found {actual_items_count}."
        )
        assert actual_total <= max_allowed_budget, (
            f"Budget exceeded: max allowed is ${max_allowed_budget:.2f}, "
            f"but cart total is ${actual_total:.2f}."
        )

        logger.info(
            "Cart verification passed: items=%s, total=$%.2f, max=$%.2f",
            actual_items_count,
            actual_total,
            max_allowed_budget,
        )
        return actual_total
