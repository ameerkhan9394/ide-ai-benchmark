#!/usr/bin/env python3
"""
Test runner script for Cursor AppImage automation tests.
Provides various test execution options.
"""

import argparse
import os
import subprocess
import sys
import time
from pathlib import Path


def run_command(cmd, env=None):
    """Run a command and return the result"""
    print(f"Running: {cmd}")
    result = subprocess.run(cmd, shell=True, capture_output=True, text=True, env=env)

    if result.stdout:
        print(result.stdout)
    if result.stderr:
        print(result.stderr, file=sys.stderr)

    return result.returncode == 0


def setup_environment():
    """Setup test environment"""
    # Create necessary directories
    directories = ["reports", "screenshots", "test_images"]
    for directory in directories:
        Path(directory).mkdir(exist_ok=True)

    # Check if Cursor AppImage exists
    cursor_path = os.getenv("CURSOR_PATH")
    if not os.path.exists(cursor_path):
        print(f"Warning: Cursor AppImage not found at {cursor_path}")
        print(
            "Please set CURSOR_PATH environment variable or ensure the AppImage exists"
        )
        return False

    print(f"Using Cursor AppImage at: {cursor_path}")
    return True


def run_basic_tests():
    """Run basic functionality tests"""
    print("=" * 60)
    print("Running Basic Functionality Tests")
    print("=" * 60)

    cmd = "uv run pytest tests/test_basic_functionality.py -v --html=reports/basic-report.html"
    return run_command(cmd)


def run_performance_tests():
    """Run performance benchmark tests"""
    print("=" * 60)
    print("Running Performance Benchmark Tests")
    print("=" * 60)

    cmd = "uv run pytest tests/test_performance_benchmarks.py -v --html=reports/performance-report.html"
    return run_command(cmd)


def run_workflow_tests():
    """Run user workflow tests"""
    print("=" * 60)
    print("Running User Workflow Tests")
    print("=" * 60)

    cmd = "uv run pytest tests/test_user_workflows.py -v --html=reports/workflow-report.html"
    return run_command(cmd)


def run_all_tests():
    """Run all tests"""
    print("=" * 60)
    print("Running All Tests")
    print("=" * 60)

    cmd = "uv run pytest tests/ -v --html=reports/all-tests-report.html"
    return run_command(cmd)


def run_quick_tests():
    """Run quick tests (excluding slow ones)"""
    print("=" * 60)
    print("Running Quick Tests (excluding slow ones)")
    print("=" * 60)

    cmd = 'uv run pytest tests/ -v -m "not slow" --html=reports/quick-report.html'
    return run_command(cmd)


def run_with_coverage():
    """Run tests with coverage reporting"""
    print("=" * 60)
    print("Running Tests with Coverage")
    print("=" * 60)

    commands = [
        "uv run coverage run -m pytest tests/ -v",
        "uv run coverage report -m",
        "uv run coverage html",
    ]

    for cmd in commands:
        if not run_command(cmd):
            return False

    print("\nCoverage report generated in htmlcov/index.html")
    return True


def create_test_image_templates():
    """Create template images for image-based testing"""
    print("=" * 60)
    print("Creating Test Image Templates")
    print("=" * 60)

    script_content = """
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from cursor_automation import CursorAutomation
import time

def main():
    app = CursorAutomation()

    print("Launching Cursor to create test images...")
    if not app.launch_app():
        print("Failed to launch Cursor")
        return False

    app.focus_window()
    time.sleep(2)

    # Create template images
    templates = [
        ("file_menu", lambda: app.key_combo('alt', 'f')),
        ("command_palette", lambda: app.key_combo('ctrl', 'shift', 'p')),
        ("new_file", lambda: app.key_combo('ctrl', 'n')),
    ]

    for template_name, action in templates:
        print(f"Creating template: {template_name}")
        action()
        time.sleep(1)

        # Take screenshot of specific region (you may need to adjust regions)
        region = (100, 100, 300, 200)  # x, y, width, height
        app.create_test_image(region, f"{template_name}.png")

        # Reset state
        app.key_combo('escape')
        time.sleep(1)

    app.close_app()
    print("Test image templates created successfully!")
    return True

if __name__ == "__main__":
    main()
"""

    with open("/tmp/create_templates.py", "w") as f:
        f.write(script_content)

    return run_command("uv run python /tmp/create_templates.py")


def main():
    parser = argparse.ArgumentParser(description="Run Cursor AppImage automation tests")
    parser.add_argument(
        "--basic", action="store_true", help="Run basic functionality tests"
    )
    parser.add_argument(
        "--performance", action="store_true", help="Run performance benchmark tests"
    )
    parser.add_argument(
        "--workflow", action="store_true", help="Run user workflow tests"
    )
    parser.add_argument("--all", action="store_true", help="Run all tests")
    parser.add_argument(
        "--quick", action="store_true", help="Run quick tests (excluding slow ones)"
    )
    parser.add_argument(
        "--coverage", action="store_true", help="Run tests with coverage"
    )
    parser.add_argument(
        "--templates", action="store_true", help="Create test image templates"
    )
    parser.add_argument(
        "--headless", action="store_true", help="Run in headless mode (requires xvfb)"
    )
    parser.add_argument("--verbose", "-v", action="store_true", help="Verbose output")

    args = parser.parse_args()

    # Setup environment
    if not setup_environment():
        sys.exit(1)

    # Set up environment variables
    env = os.environ.copy()

    # If headless mode, use xvfb
    if args.headless:
        env["DISPLAY"] = ":99"
        print("Running in headless mode...")
        subprocess.Popen(
            ["Xvfb", ":99", "-screen", "0", "1920x1080x24"],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        time.sleep(2)  # Give Xvfb time to start

    success = True

    if args.templates:
        success &= create_test_image_templates()
    elif args.basic:
        success &= run_basic_tests()
    elif args.performance:
        success &= run_performance_tests()
    elif args.workflow:
        success &= run_workflow_tests()
    elif args.all:
        success &= run_all_tests()
    elif args.quick:
        success &= run_quick_tests()
    elif args.coverage:
        success &= run_with_coverage()
    else:
        print("No test type specified. Running quick tests by default.")
        success &= run_quick_tests()

    if success:
        print("\n✅ Tests completed successfully!")
    else:
        print("\n❌ Tests failed!")
        sys.exit(1)


if __name__ == "__main__":
    main()
