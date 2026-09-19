# ReadMeAIBugs – בדיקה סטטית של הקוד

להלן הבעיות שמצאתי בקוד שסופק בתרגיל, יחד עם הסבר קצר ותיקון מוצע.

## 1. ייבוא מיותר של Selenium

### הבעיה
בקוד קיים:

```python
from selenium import webdriver
```

אבל בפועל הבדיקה כתובה עם Playwright בלבד ואין שימוש ב-Selenium.

### למה זו בעיה
זה מוסיף תלות מיותרת ומבלבל לגבי כלי האוטומציה שבו משתמשים.

### תיקון
להסיר את הייבוא של Selenium ולהשאיר רק את הייבואים שנדרשים בפועל.

---

## 2. הפעלה לא מסודרת של Playwright

### הבעיה
Playwright מופעל באמצעות:

```python
browser = sync_playwright().start().chromium.launch()
```

אבל בסוף נסגר רק ה-browser ולא מופע Playwright עצמו.

### למה זו בעיה
במקרה של כשל באמצע הריצה עלולים להישאר משאבים או תהליכים פתוחים.

### תיקון
עדיף להשתמש ב-context manager:

```python
with sync_playwright() as p:
    browser = p.chromium.launch()
```

כך Playwright נסגר בצורה מסודרת בסיום הריצה.

---

## 3. שימוש ב-`time.sleep()`

### הבעיה
הקוד משתמש בהמתנות קבועות:

```python
time.sleep(2)
time.sleep(3)
```

### למה זו בעיה
זמן קבוע לא מבטיח שהעמוד או האלמנט באמת מוכנים. במחשב מהיר מבוזבז זמן, ובמחשב איטי ההמתנה עלולה לא להספיק.

### תיקון
להשתמש בהמתנות של Playwright, לדוגמה:

```python
search_box.wait_for(state="visible", timeout=5000)
```

---

## 4. אין Assertion לתוצאות החיפוש

### הבעיה
הקוד יוצר Locator לתוצאות:

```python
results = page.locator(".result-item")
```

אבל לא בודק שנמצאו תוצאות.

### למה זו בעיה
הטסט יכול להסתיים בלי לוודא שהפעולה שבדקנו באמת הצליחה.

### תיקון
להוסיף בדיקה מפורשת:

```python
assert results.count() > 0, "No search results were found"
```

---

## 5. Locator כללי מדי לכפתור

### הבעיה
הקוד משתמש ב:

```python
page.locator(".button").click()
```

### למה זו בעיה
המחלקה `.button` יכולה להתאים ליותר מכפתור אחד, ולכן הקוד עלול ללחוץ על אלמנט לא נכון.

### תיקון
להשתמש ב-Locator יותר ממוקד, למשל:

```python
page.locator("#searchBtn").click()
```

או:

```python
page.get_by_role("button", name="Search").click()
```

---

## 6. אין הבטחה שהדפדפן ייסגר במקרה של שגיאה

### הבעיה
`browser.close()` נמצא בסוף הקוד בלבד. אם תתרחש חריגה לפני השורה הזאת, ייתכן שהדפדפן לא ייסגר.

### תיקון
להשתמש ב-`try/finally` או ב-`with sync_playwright()` כדי להבטיח סגירה גם במקרה של כשל.

---

## 7. אין Logging

### הבעיה
אין בקוד תיעוד של שלבי הריצה, לדוגמה פתיחת העמוד, ביצוע חיפוש, מספר תוצאות או שגיאות.

### למה זו בעיה
כאשר הטסט נכשל קשה להבין באיזה שלב הבעיה התרחשה ומה גרם לה.

### תיקון
להוסיף מנגנון Logging:

```python
import logging

logger = logging.getLogger(__name__)
logger.info("Opening search page")
logger.info("Submitting search query")
```

ובמקרה של חריגה:

```python
logger.exception("Search test failed")
```

---

## 8. אין טיפול במצבי `None` או בערכים/אלמנטים חסרים

### הבעיה
הקוד מניח שכל הנתונים והאלמנטים קיימים. אין בדיקה מפורשת לערך `None` או למצב שבו אלמנט נדרש לא נמצא.

ב-Python אין `NullPointerException` כמו ב-Java, אבל עדיין צריך לטפל במצבים שבהם ערך הוא `None` או שחסר נתון נדרש.

### תיקון
לדוגמה, אפשר לבדוק ערך לפני שימוש בו:

```python
result_link = results.first.get_attribute("href")

if result_link is None:
    raise ValueError("Result URL was not found")
```

ובמקרה של Locator:

```python
search_box = page.locator("#search")

if search_box.count() == 0:
    raise ValueError("Search input was not found")
```

---

## דוגמה לקוד מתוקן

```python
import logging
from playwright.sync_api import sync_playwright, expect

logger = logging.getLogger(__name__)


def test_search_functionality():
    with sync_playwright() as p:
        browser = p.chromium.launch()

        try:
            page = browser.new_page()
            logger.info("Opening search page")
            page.goto("https://example.com")

            search_box = page.locator("#search")

            if search_box.count() == 0:
                logger.error("Search input was not found")
                raise ValueError("Search input was not found")

            search_box.wait_for(state="visible", timeout=5000)

            query = "playwright testing"

            if query is None or not query.strip():
                logger.error("Search query is empty or None")
                raise ValueError("Search query must not be empty or None")

            search_box.fill(query)

            search_button = page.locator("#searchBtn")

            if search_button.count() == 0:
                logger.error("Search button was not found")
                raise ValueError("Search button was not found")

            logger.info("Submitting search query")
            search_button.click()

            results = page.locator(".result-item")

            if results.count() == 0:
                logger.error("No search results were found")
                raise AssertionError("No search results were found")

            expect(results.first).to_be_visible()

            result_link = results.first.get_attribute("href")

            if result_link is None:
                logger.error("Result URL is None")
                raise ValueError("Result URL was not found")

            logger.info("Search completed successfully. Results found: %s", results.count())

        except Exception:
            logger.exception("Search test failed")
            raise

        finally:
            browser.close()
```
