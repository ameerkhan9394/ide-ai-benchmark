#!/usr/bin/env python3

import os
import subprocess
import sys
import time


def check_display():
    """Check if DISPLAY is properly set"""
    display = os.environ.get("DISPLAY")
    print(f"DISPLAY environment variable: {display}")
    return display is not None


def check_xvfb():
    """Check if Xvfb is running"""
    try:
        result = subprocess.run(["pgrep", "Xvfb"], capture_output=True, text=True)
        if result.returncode == 0:
            pid = result.stdout.strip()
            print(f"Xvfb is running with PID: {pid}")
            return True
        else:
            print("Xvfb is not running")
            return False
    except Exception as e:
        print(f"Error checking Xvfb: {e}")
        return False


def check_window_manager():
    """Check if window manager is running"""
    try:
        result = subprocess.run(["pgrep", "fluxbox"], capture_output=True, text=True)
        if result.returncode == 0:
            pid = result.stdout.strip()
            print(f"Fluxbox is running with PID: {pid}")
            return True
        else:
            print("Fluxbox is not running")
            return False
    except Exception as e:
        print(f"Error checking window manager: {e}")
        return False


def check_x11_connection():
    """Test X11 connection with xdpyinfo"""
    try:
        result = subprocess.run(["xdpyinfo"], capture_output=True, text=True, timeout=5)
        if result.returncode == 0:
            print("X11 connection is working")
            # Print some basic info
            lines = result.stdout.split("\n")
            for line in lines[:10]:  # First 10 lines
                if line.strip():
                    print(f"  {line}")
            return True
        else:
            print("X11 connection failed")
            print("Error:", result.stderr)
            return False
    except subprocess.TimeoutExpired:
        print("X11 connection test timed out")
        return False
    except Exception as e:
        print(f"Error testing X11 connection: {e}")
        return False


def check_pyautogui():
    """Test if pyautogui can access the display"""
    try:
        # First check if the module can be imported
        import subprocess
        import sys

        # Test import in subprocess to avoid X11 connection at module level
        # Use the virtual environment's python
        python_path = "/home/testuser/cursor-benchmark/.venv/bin/python"
        result = subprocess.run(
            [
                python_path,
                "-c",
                'import pyautogui; size = pyautogui.size(); print(f"Screen size: {size}")',
            ],
            capture_output=True,
            text=True,
            timeout=10,
        )

        if result.returncode == 0:
            print(f"PyAutoGUI working: {result.stdout.strip()}")
            return True
        else:
            print(f"PyAutoGUI error: {result.stderr.strip()}")
            return False

    except subprocess.TimeoutExpired:
        print("PyAutoGUI test timed out")
        return False
    except Exception as e:
        print(f"PyAutoGUI test error: {e}")
        return False


def check_cursor_appimage():
    """Check if Cursor AppImage exists and is executable"""
    cursor_path = os.environ.get(
        "CURSOR_PATH", "/home/testuser/Applications/cursor.AppImage"
    )

    if os.path.exists(cursor_path):
        if os.access(cursor_path, os.X_OK):
            print(f"Cursor AppImage found and executable: {cursor_path}")
            return True
        else:
            print(f"Cursor AppImage found but not executable: {cursor_path}")
            return False
    else:
        print(f"Cursor AppImage not found: {cursor_path}")
        return False


def main():
    """Run all environment checks"""
    print("=== Environment Verification ===")
    print()

    checks = [
        ("DISPLAY Environment", check_display),
        ("Xvfb Process", check_xvfb),
        ("Window Manager", check_window_manager),
        ("X11 Connection", check_x11_connection),
        ("PyAutoGUI", check_pyautogui),
        ("Cursor AppImage", check_cursor_appimage),
    ]

    results = []
    for name, check_func in checks:
        print(f"Checking {name}...")
        try:
            result = check_func()
            results.append((name, result))
            print(f"✅ {name}: {'PASS' if result else 'FAIL'}")
        except Exception as e:
            print(f"❌ {name}: ERROR - {e}")
            results.append((name, False))
        print()

    # Summary
    print("=== Summary ===")
    passed = sum(1 for _, result in results if result)
    total = len(results)

    for name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status} {name}")

    print(f"\nOverall: {passed}/{total} checks passed")

    if passed == total:
        print("🎉 Environment is ready for testing!")
        return 0
    else:
        print("🚨 Environment has issues that need to be fixed")
        return 1


if __name__ == "__main__":
    sys.exit(main())
