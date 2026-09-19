import logging

from playwright.sync_api import Page

from pages.cart_page import CartPage
from pages.login_page import LoginPage
from pages.product_page import ProductPage
from pages.search_page import SearchPage


logger = logging.getLogger(__name__)


def test_ebay_shopping_cart_e2e(
    page: Page,
    mock_server: str,
    test_data: dict,
    run_report_data: dict,
):
    search_page = SearchPage(page)
    login_page = LoginPage(page)
    product_page = ProductPage(page)
    cart_page = CartPage(page)

    run_report_data.update(
        {
            "query": test_data["search_query"],
            "budget_per_item": float(test_data["max_price"]),
            "limit": int(test_data["item_limit"]),
        }
    )

    # 1. Open the mock store and authenticate.
    search_page.navigate(mock_server)
    login_page.login(
        username=test_data["username"],
        password=test_data["password"],
    )
    run_report_data["login_username"] = test_data["username"]
    run_report_data["login_status"] = "Authenticated"
    run_report_data["login_type"] = "Stub Login"

    # 2. Search and collect up to item_limit matching URLs under max_price.
    urls = search_page.search_items_by_name_under_price(
        query=test_data["search_query"],
        max_price=float(test_data["max_price"]),
        limit=int(test_data["item_limit"]),
    )
    run_report_data["products"] = list(search_page.last_matches)
    run_report_data["items_count"] = len(urls)
    run_report_data["max_total"] = float(test_data["max_price"]) * len(urls)

    logger.info("Matching products found: %s", len(urls))
    for index, product in enumerate(search_page.last_matches, start=1):
        logger.info(
            "Product #%s: %s | $%.2f",
            index,
            product["name"],
            product["price"],
        )

    # 3. Add every returned product to the cart.
    added_products = product_page.add_items_to_cart(urls)
    run_report_data["added_products"] = added_products

    variants_by_url = {
        product["url"]: product.get("variants", {})
        for product in added_products
    }
    for product in run_report_data["products"]:
        product["variants"] = variants_by_url.get(product["url"], {})
        product["added"] = product["url"] in variants_by_url

    # 4. Open the cart and verify its total against the allowed budget.
    actual_total = cart_page.assert_cart_total_not_exceeds(
        budget_per_item=float(test_data["max_price"]),
        items_count=len(urls),
    )
    run_report_data["actual_total"] = actual_total
