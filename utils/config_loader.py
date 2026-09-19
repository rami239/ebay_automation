import json
import os
from pathlib import Path
from typing import Any, Dict


_REQUIRED_KEYS = {
    "username",
    "password",
    "search_query",
    "max_price",
    "item_limit",
}


def load_test_data(path: str | Path | None = None) -> Dict[str, Any]:
    """Load test inputs from JSON. TEST_DATA_FILE may override the default file."""
    project_root = Path(__file__).resolve().parents[1]
    configured_path = path or os.getenv("TEST_DATA_FILE")
    data_path = Path(configured_path) if configured_path else project_root / "config" / "data.json"

    if not data_path.is_file():
        raise FileNotFoundError(f"Test data file was not found: {data_path}")

    with data_path.open("r", encoding="utf-8") as file:
        data = json.load(file)

    missing = _REQUIRED_KEYS - data.keys()
    if missing:
        raise ValueError(f"Missing required test-data keys: {sorted(missing)}")

    if float(data["max_price"]) < 0:
        raise ValueError("max_price must be greater than or equal to 0.")
    if int(data["item_limit"]) < 0:
        raise ValueError("item_limit must be greater than or equal to 0.")

    return data
