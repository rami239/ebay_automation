import logging

from playwright.sync_api import Page, expect

from pages.base_page import BasePage


logger = logging.getLogger(__name__)


class LoginPage(BasePage):
    def __init__(self, page: Page):
        super().__init__(page)
        self.username_input = "#username"
        self.password_input = "#password"
        self.login_button = "#loginBtn"
        self.login_status = "#loginStatus"

    def login(self, username: str, password: str) -> None:
        if not username or not password:
            raise ValueError("Username and password must not be empty.")

        logger.info("Authenticating user: %s", username)

        self.page.locator(self.username_input).fill(username)
        self.page.locator(self.password_input).fill(password)
        self.page.locator(self.login_button).click()

        status = self.page.locator(self.login_status)
        expect(status).to_have_text("Logged in", timeout=5000)

        logger.info("Login successful for user: %s", username)
        self.take_screenshot("Login_Success")
