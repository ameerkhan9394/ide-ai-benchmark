import logging
import os
import sys
import time
from typing import Generator

import pytest

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from cursor_automation import CursorAutomation

# Configure test logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Global app instance to prevent multiple launches
_app_instance = None


@pytest.fixture(scope="session")
def cursor_app_session(request) -> Generator[CursorAutomation, None, None]:
    """Session-scoped fixture that launches Cursor once for all tests"""
    global _app_instance

    if _app_instance is None:
        logger.info("=== LAUNCHING CURSOR FOR TEST SESSION ===")

        # Get cursor path from command line if provided
        cursor_path = request.config.getoption("--cursor-path")
        _app_instance = CursorAutomation(appimage_path=cursor_path)

        logger.info(f"Using Cursor AppImage: {_app_instance.appimage_path}")

        # Try to launch with extended timeout
        success = _app_instance.launch_app(timeout=30)
        if not success:
            logger.error("Failed to launch Cursor for test session")
            pytest.exit("Could not launch Cursor AppImage")

        logger.info("=== CURSOR SESSION READY ===")

    yield _app_instance

    # Cleanup at end of session
    if _app_instance:
        logger.info("=== CLOSING CURSOR SESSION ===")
        _app_instance.close_app()
        _app_instance = None


@pytest.fixture
def cursor_app(cursor_app_session) -> Generator[CursorAutomation, None, None]:
    """Function-scoped fixture that provides a clean app state for each test"""
    app = cursor_app_session

    # Reset to clean state before each test
    logger.info(f"=== PREPARING TEST: {pytest.current_test_name} ===")

    # Focus window
    app.focus_window()
    time.sleep(0.5)

    # Close any open dialogs/menus
    for _ in range(3):
        app.key_combo("escape")
        time.sleep(0.1)

    # Close all tabs except one
    app.key_combo("ctrl", "shift", "w")  # Close all tabs
    time.sleep(0.5)

    # Open a new file to have clean state
    app.key_combo("ctrl", "n")
    time.sleep(0.5)

    yield app

    # Cleanup after each test
    logger.info(f"=== CLEANING UP TEST: {pytest.current_test_name} ===")

    # Take screenshot for debugging if test failed
    if hasattr(pytest, "failed") and pytest.failed:
        screenshot_name = f"failed_{pytest.current_test_name}_{int(time.time())}.png"
        app.take_screenshot(screenshot_name)
        logger.error(f"Test failed - screenshot saved: {screenshot_name}")

    # Close any dialogs
    for _ in range(3):
        app.key_combo("escape")
        time.sleep(0.1)

    # Close all tabs
    app.key_combo("ctrl", "shift", "w")
    time.sleep(0.5)


@pytest.fixture(autouse=True)
def setup_test_info(request):
    """Auto-used fixture to set current test name for logging"""
    pytest.current_test_name = request.node.name
    logger.info(f"STARTING TEST: {request.node.name}")

    yield

    logger.info(f"COMPLETED TEST: {request.node.name}")


def pytest_sessionstart(session):
    """Called after the Session object has been created"""
    logger.info("=== PYTEST SESSION STARTING ===")

    # Create necessary directories
    os.makedirs("screenshots", exist_ok=True)
    os.makedirs("test_images", exist_ok=True)
    os.makedirs("reports", exist_ok=True)


def pytest_sessionfinish(session, exitstatus):
    """Called after whole test run finished"""
    logger.info(f"=== PYTEST SESSION FINISHED (exit status: {exitstatus}) ===")


def pytest_runtest_setup(item):
    """Called before each test item is run"""
    logger.info(f"Setting up test: {item.name}")


def pytest_runtest_teardown(item, nextitem):
    """Called after each test item is run"""
    logger.info(f"Tearing down test: {item.name}")


def pytest_runtest_makereport(item, call):
    """Called after each test phase (setup, call, teardown)"""
    if call.when == "call":
        # Mark if test failed for screenshot capture
        if call.excinfo is not None:
            pytest.failed = True
        else:
            pytest.failed = False


# Configure pytest markers
def pytest_configure(config):
    """Configure pytest markers"""
    config.addinivalue_line(
        "markers", "slow: marks tests as slow (deselect with '-m \"not slow\"')"
    )
    config.addinivalue_line("markers", "integration: marks tests as integration tests")
    config.addinivalue_line("markers", "unit: marks tests as unit tests")


# Add custom command line options
def pytest_addoption(parser):
    """Add custom command line options"""
    parser.addoption(
        "--cursor-path",
        action="store",
        help="Path to Cursor AppImage (auto-detected if not specified)",
    )
    parser.addoption(
        "--keep-cursor-open",
        action="store_true",
        help="Keep Cursor open after tests finish",
    )
    parser.addoption(
        "--no-screenshots",
        action="store_true",
        help="Disable screenshot capture for failed tests",
    )
