#!/usr/bin/env python3
"""
Setup script for Cursor AppImage Testing Framework
"""

import argparse
import os
import subprocess
import sys
from pathlib import Path

from dotenv import load_dotenv


def run_command(cmd, check=True):
    """Run a command and handle errors"""
    print(f"Running: {cmd}")
    try:
        result = subprocess.run(
            cmd, shell=True, check=check, capture_output=True, text=True
        )
        if result.stdout:
            print(result.stdout)
        return True
    except subprocess.CalledProcessError as e:
        print(f"Error: {e}")
        if e.stderr:
            print(f"stderr: {e.stderr}")
        return False


def check_system_requirements():
    """Check if system requirements are met"""
    print("Checking system requirements...")

    # Check Python version
    if sys.version_info < (3, 9):
        print("ERROR: Python 3.9 or higher is required")
        return False

    print(f"✓ Python {sys.version_info.major}.{sys.version_info.minor}")

    # Check if running on Linux
    if os.name != "posix":
        print("WARNING: This framework is designed for Linux systems")

    # Check for required system packages
    required_packages = ["xvfb", "xdotool", "scrot"]
    missing_packages = []

    for package in required_packages:
        if not run_command(f"which {package}", check=False):
            missing_packages.append(package)

    if missing_packages:
        print(f"Missing system packages: {missing_packages}")
        print(
            "Install them with: sudo apt-get install -y " + " ".join(missing_packages)
        )
        return False

    return True


def create_directories():
    """Create necessary directories"""
    print("Creating project directories...")

    directories = ["reports", "screenshots", "test_images", "logs"]

    for directory in directories:
        Path(directory).mkdir(exist_ok=True)
        print(f"✓ Created {directory}/")


def install_dependencies():
    """Install Python dependencies"""
    print("Installing Python dependencies...")

    if not run_command("pip install -r requirements.txt"):
        print("ERROR: Failed to install requirements")
        return False

    # Install additional development dependencies
    dev_packages = ["pytest-cov", "pytest-html", "black", "flake8", "coverage"]

    for package in dev_packages:
        run_command(f"pip install {package}", check=False)

    return True


def check_cursor_appimage():
    """Check if Cursor AppImage exists"""
    print("Checking Cursor AppImage...")

    # Load environment variables from .env file
    load_dotenv()

    cursor_path = os.getenv("CURSOR_PATH")
    if not cursor_path:
        print("ERROR: CURSOR_PATH not set in environment or .env file")
        return False

    if not os.path.exists(cursor_path):
        print(f"WARNING: Cursor AppImage not found at {cursor_path}")
        print(
            "Please ensure the AppImage exists or set CURSOR_PATH environment variable"
        )
        return False

    # Check if it's executable
    if not os.access(cursor_path, os.X_OK):
        print(f"Making {cursor_path} executable...")
        run_command(f"chmod +x {cursor_path}")

    print(f"✓ Cursor AppImage found at {cursor_path}")
    return True


def setup_git_hooks():
    """Setup Git hooks for development"""
    print("Setting up Git hooks...")

    if not os.path.exists(".git"):
        print("Not a Git repository, skipping hooks setup")
        return

    # Create pre-commit hook
    hook_content = """#!/bin/bash
# Pre-commit hook for Cursor AppImage Testing Framework

echo "Running pre-commit checks..."

# Format code
black src/ tests/ scripts/

# Run linters
flake8 src/ tests/ scripts/
if [ $? -ne 0 ]; then
    echo "Linting failed. Please fix the issues."
    exit 1
fi

# Run quick tests
python scripts/run_tests.py --quick
if [ $? -ne 0 ]; then
    echo "Tests failed. Please fix the issues."
    exit 1
fi

echo "Pre-commit checks passed!"
"""

    hook_path = ".git/hooks/pre-commit"
    with open(hook_path, "w") as f:
        f.write(hook_content)

    run_command(f"chmod +x {hook_path}")
    print("✓ Git pre-commit hook installed")


def create_sample_test():
    """Create a sample test file"""
    print("Creating sample test...")

    sample_test = '''import pytest
import sys
import os

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from cursor_automation import CursorAutomation


def test_sample():
    """Sample test to verify the framework works"""
    app = CursorAutomation()

    # Test app launch
    assert app.launch_app(), "Should be able to launch Cursor"

    # Test window properties
    window_info = app.get_window_info()
    assert window_info, "Should get window info"

    # Test screenshot
    screenshot = app.take_screenshot("sample_test.png")
    assert os.path.exists(screenshot), "Should create screenshot"

    # Cleanup
    app.close_app()

    print("✓ Sample test passed!")


if __name__ == "__main__":
    test_sample()
'''

    with open("tests/test_sample.py", "w") as f:
        f.write(sample_test)

    print("✓ Sample test created at tests/test_sample.py")


def main():
    parser = argparse.ArgumentParser(
        description="Setup Cursor AppImage Testing Framework"
    )
    parser.add_argument(
        "--check-only", action="store_true", help="Only check requirements"
    )
    parser.add_argument(
        "--no-deps", action="store_true", help="Skip dependency installation"
    )
    parser.add_argument(
        "--no-cursor-check", action="store_true", help="Skip Cursor AppImage check"
    )
    parser.add_argument("--dev", action="store_true", help="Setup for development")

    args = parser.parse_args()

    print("=" * 60)
    print("Cursor AppImage Testing Framework Setup")
    print("=" * 60)

    # Check system requirements
    if not check_system_requirements():
        print("❌ System requirements not met")
        sys.exit(1)

    if args.check_only:
        print("✅ System requirements check passed")
        return

    # Create directories
    create_directories()

    # Install dependencies
    if not args.no_deps:
        if not install_dependencies():
            print("❌ Failed to install dependencies")
            sys.exit(1)

    # Check Cursor AppImage
    if not args.no_cursor_check:
        check_cursor_appimage()

    # Make scripts executable
    run_command("chmod +x scripts/run_tests.py")

    if args.dev:
        # Setup development environment
        setup_git_hooks()
        create_sample_test()

    print("\n" + "=" * 60)
    print("✅ Setup completed successfully!")
    print("=" * 60)
    print("\nNext steps:")
    print("1. Run a sample test: python tests/test_sample.py")
    print("2. Run all tests: make test")
    print("3. Run specific tests: make test-basic")
    print("4. Check the README.md for detailed usage instructions")
    print("\nHappy testing! 🎉")


if __name__ == "__main__":
    main()
