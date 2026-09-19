import re


_PRICE_PATTERN = re.compile(r"\d+(?:,\d{3})*(?:\.\d+)?")


def parse_price(text: str) -> float:
    """Parse the first monetary numeric value from text such as '$1,234.56'."""
    if not text or not text.strip():
        raise ValueError("Price text must not be empty.")

    match = _PRICE_PATTERN.search(text)
    if not match:
        raise ValueError(f"Could not parse price from: {text!r}")

    return float(match.group(0).replace(",", ""))
