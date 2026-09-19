# eBay Mock E2E Automation – Python + Playwright

This project implements the supplied automation exercise using **Python, Playwright, pytest, OOP, Page Object Model (POM), SRP and Data-Driven configuration**.

## Automated flow

1. Open the supplied mock store.
2. Perform the stub login using credentials from `config/data.json`.
3. Search by query and collect up to the requested limit of product URLs whose displayed price is `<= max_price`.
4. Use paging until the limit is reached or there are no more pages.
5. Open every collected product URL.
6. Randomly select every available variant (size/color/etc.).
7. Add the product to the cart and verify that the cart counter increased.
8. Save a screenshot for every successfully added product.
9. Return to the search page after every product.
10. Open the cart through the UI, read the displayed total and assert that it does not exceed `budget_per_item * items_count`.
11. Save a final cart screenshot.

## Installation

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
playwright install chromium
```

## Run

```powershell
pytest --headed
```

## Reports and logs

After each run:

- `artifacts/report.html` – main human-readable HTML execution report with login status, products, prices, selected random variants, cart totals and screenshots.
- `artifacts/run.log` – persistent execution log.
- `artifacts/junit.xml` – standard pytest JUnit XML report.
- `artifacts/screenshots/` – screenshots from the flow.

The project intentionally **does not depend on pytest-html**. `pytest-html 4.x` can generate an empty result table in some environments even when pytest reports passed tests, so the main HTML report is generated directly from the test data and pytest result. The installed `pytest-html` plugin, if present in the virtual environment, is explicitly disabled through `-p no:html` in `pytest.ini`.

## Architecture

- `pages/base_page.py` – shared page behavior such as screenshots.
- `pages/login_page.py` – authentication page object.
- `pages/search_page.py` – query, XPath result extraction, price parsing and paging.
- `pages/product_page.py` – random variant selection and add-to-cart flow.
- `pages/cart_page.py` – cart opening, total parsing and assertions.
- `utils/config_loader.py` – JSON data loading.
- `utils/price_parser.py` – price parsing utility.
- `utils/report_builder.py` – self-contained HTML report generation.
- `tests/test_ebay_e2e.py` – complete E2E scenario.
- `ReadMeAIBugs.md` – static analysis of the AI-generated code supplied in the exercise.

## Assumptions / limitations

- The exercise is executed against the supplied local eBay-style mock pages, not the live `ebay.com` website.
- Login is a **Stub Login**: the supplied mock accepts any non-empty username/password pair.
- Prices are treated as USD because the supplied mock uses `$`.
- Product URLs are temporary localhost URLs while the test runs. The persistent HTML report therefore stores the mock page filename instead of a dead localhost hyperlink.
