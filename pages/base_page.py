from pathlib import Path
import re
from playwright.sync_api import Page


class BasePage:
    """Base class shared by all Page Objects."""

    def __init__(self, page: Page):
        self.page = page

    def take_screenshot(self, name: str) -> Path:
        """Save a screenshot under artifacts/screenshots and return its path."""
        project_root = Path(__file__).resolve().parents[1]
        screenshots_dir = project_root / "artifacts" / "screenshots"
        screenshots_dir.mkdir(parents=True, exist_ok=True)

        safe_name = re.sub(r"[^A-Za-z0-9_.-]+", "_", name).strip("_") or "screenshot"
        screenshot_path = screenshots_dir / f"{safe_name}.png"
        self.page.screenshot(path=str(screenshot_path), full_page=False)
        return screenshot_path
