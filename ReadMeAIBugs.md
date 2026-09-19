# AI Bugs - Static Code Review

The exercise asks for a static review of the provided code and at least three identified problems, explanations, and suggested fixes.

## Original code issues

### 1. Async Playwright is imported, but `sync_playwright()` is called

The code imports:

```python
from playwright.async_api import async_playwright
```

but later calls:

```python
browser = sync_playwright().start().chromium.launch()
```

`sync_playwright` is not imported, so this raises `NameError`. The code also mixes the async API choice with synchronous usage.

**Fix - choose one API consistently.** For a synchronous pytest test:

```python
from playwright.sync_api import sync_playwright

with sync_playwright() as playwright:
    browser = playwright.chromium.launch()
```

Alternatively, keep `async_playwright`, make the test asynchronous, and use `await` consistently.

---

### 2. `time.sleep()` creates hard waits and flaky/slow tests

The code uses:

```python
time.sleep(2)
...
time.sleep(3)
```

A fixed delay does not prove that the application is ready. If the UI is slower, the wait may be insufficient; if it is faster, the test wastes time.

**Fix:** rely on Playwright auto-waiting and explicit state-based waits when needed:

```python
search_box = page.locator("#search")
search_box.fill("playwright testing")
page.locator("#searchBtn").click()
page.locator(".result-item").first.wait_for(state="visible")
```

---

### 3. The test never asserts the search result

The code only creates a locator:

```python
results = page.locator(".result-item")
```

but does not verify that results exist or contain the expected data. A test with no meaningful assertion can pass even when the feature is broken.

**Fix:** add an assertion, for example:

```python
from playwright.sync_api import expect

results = page.locator(".result-item")
expect(results.first).to_be_visible()
assert results.count() > 0, "Expected at least one search result."
```

---

### 4. The `.button` locator is too generic

The code clicks:

```python
page.locator(".button").click()
```

A generic class may match multiple unrelated buttons and makes the test fragile when the page changes.

**Fix:** use a locator that identifies the intended control, for example:

```python
page.locator("#searchBtn").click()
```

or, when accessible markup is available:

```python
page.get_by_role("button", name="Search").click()
```

---

### 5. Selenium is imported but never used

The code contains:

```python
from selenium import webdriver
```

but the implementation uses Playwright only. This is dead code and adds unnecessary confusion/dependency.

**Fix:** remove the Selenium import.

---

### 6. Browser cleanup is not exception-safe

The code calls `browser.close()` only at the end. If an earlier step raises an exception, cleanup may not occur.

**Fix:** use the Playwright context manager so resources are cleaned up even on failure:

```python
from playwright.sync_api import sync_playwright

with sync_playwright() as playwright:
    browser = playwright.chromium.launch()
    page = browser.new_page()
    # test steps
    browser.close()
```

In a pytest + `pytest-playwright` project, it is even cleaner to use the provided `page` fixture and let pytest manage browser lifecycle.
