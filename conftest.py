import os
import threading
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

import pytest

from utils.config_loader import load_test_data
from utils.report_builder import write_execution_report


PROJECT_ROOT = Path(__file__).resolve().parent
ARTIFACTS_DIR = PROJECT_ROOT / "artifacts"
SCREENSHOTS_DIR = ARTIFACTS_DIR / "screenshots"
ARTIFACTS_DIR.mkdir(parents=True, exist_ok=True)
SCREENSHOTS_DIR.mkdir(parents=True, exist_ok=True)

_RUN_REPORT: dict = {}


class QuietHTTPRequestHandler(SimpleHTTPRequestHandler):
    def log_message(self, format, *args):
        pass


@pytest.fixture(scope="session")
def browser_type_launch_args(browser_type_launch_args):
    """Optional slow motion for demonstrations: set SLOW_MO_MS=300, for example."""
    slow_mo = int(os.getenv("SLOW_MO_MS", "0"))
    return {
        **browser_type_launch_args,
        "slow_mo": slow_mo,
    }


@pytest.fixture(scope="session")
def mock_server():
    """Serve the mock store over HTTP so all pages share the same localStorage origin."""
    config_dir = PROJECT_ROOT / "config"
    handler = partial(QuietHTTPRequestHandler, directory=str(config_dir))
    server = ThreadingHTTPServer(("127.0.0.1", 0), handler)

    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()

    try:
        yield f"http://127.0.0.1:{server.server_port}"
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=5)


@pytest.fixture(scope="session")
def test_data():
    return load_test_data()


@pytest.fixture
def run_report_data():
    """Mutable data bag used to build a readable, persistent HTML summary."""
    for screenshot in SCREENSHOTS_DIR.glob("*.png"):
        screenshot.unlink(missing_ok=True)
    _RUN_REPORT.clear()
    _RUN_REPORT.update(
        {
            "status": "RUNNING",
            "products": [],
            "items_count": 0,
            "actual_total": None,
            "error": "",
        }
    )
    return _RUN_REPORT


@pytest.hookimpl(hookwrapper=True)
def pytest_runtest_makereport(item, call):
    outcome = yield
    report = outcome.get_result()

    if report.when == "call":
        _RUN_REPORT["status"] = "PASSED" if report.passed else "FAILED"
        _RUN_REPORT["duration"] = report.duration
        if report.failed:
            _RUN_REPORT["error"] = str(report.longrepr)


def pytest_sessionfinish(session, exitstatus):
    # Always create the readable report, even when a test fails midway.
    if not _RUN_REPORT:
        _RUN_REPORT.update({"status": "NO TEST DATA", "products": []})
    write_execution_report(
        _RUN_REPORT,
        ARTIFACTS_DIR / "report.html",
        SCREENSHOTS_DIR,
    )
