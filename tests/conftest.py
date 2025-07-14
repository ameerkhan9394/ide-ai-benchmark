import os
import sys

import pytest

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from ide_automation import create_ide_automation


@pytest.fixture(scope="session")
def ide_name(request):
    """Get IDE name from command line or default to cursor"""
    return request.config.getoption("--ide", default="cursor")


@pytest.fixture(scope="session")
def ide_app(ide_name):
    """Fixture to provide IDE automation instance for the session"""
    app = create_ide_automation(ide_name)

    # Launch the IDE
    assert app.launch_app(), f"Failed to launch {ide_name} IDE"

    yield app

    # Cleanup
    app.close_app()


@pytest.fixture
def ide_focused(ide_app):
    """Fixture to ensure IDE window is focused for each test"""
    ide_app.focus_window()
    yield ide_app


@pytest.fixture(params=["cursor", "windsurf", "vscode"])
def multi_ide_app(request):
    """Fixture for testing across multiple IDEs"""
    ide_name = request.param

    # Skip if IDE is not available
    try:
        app = create_ide_automation(ide_name)
        if not app.launch_app():
            pytest.skip(f"{ide_name} IDE not available or failed to launch")
    except Exception as e:
        pytest.skip(f"{ide_name} IDE not supported: {e}")

    yield app
    app.close_app()


@pytest.fixture
def ai_models(ide_app):
    """Fixture to get available AI models for the current IDE"""
    return ide_app.get_ai_models()


def pytest_addoption(parser):
    """Add command line options for IDE selection"""
    parser.addoption(
        "--ide",
        action="store",
        default="cursor",
        help="IDE to test (cursor, windsurf, vscode, etc.)",
        choices=["cursor", "windsurf", "vscode"]
    )

    parser.addoption(
        "--model",
        action="store",
        default=None,
        help="AI model to test (claude-3.5-sonnet, gpt-4, etc.)"
    )

    parser.addoption(
        "--headless",
        action="store_true",
        default=False,
        help="Run in headless mode"
    )


def pytest_configure(config):
    """Configure pytest with custom markers"""
    config.addinivalue_line(
        "markers", "slow: marks tests as slow (deselect with '-m \"not slow\"')"
    )
    config.addinivalue_line(
        "markers", "cursor: marks tests specific to Cursor IDE"
    )
    config.addinivalue_line(
        "markers", "windsurf: marks tests specific to Windsurf IDE"
    )
    config.addinivalue_line(
        "markers", "vscode: marks tests specific to VSCode"
    )
    config.addinivalue_line(
        "markers", "cross_ide: marks tests that run across multiple IDEs"
    )
    config.addinivalue_line(
        "markers", "ai_model: marks tests that test AI model functionality"
    )


def pytest_collection_modifyitems(config, items):
    """Modify test collection based on command line options"""
    ide_name = config.getoption("--ide")

    # Add IDE-specific markers
    for item in items:
        if ide_name in item.nodeid.lower():
            item.add_marker(getattr(pytest.mark, ide_name))

        # Mark tests that use multi_ide_app fixture as cross_ide
        if "multi_ide_app" in item.fixturenames:
            item.add_marker(pytest.mark.cross_ide)

        # Mark tests that test AI functionality
        if any(keyword in item.name.lower() for keyword in ["ai", "model", "completion", "chat"]):
            item.add_marker(pytest.mark.ai_model)
