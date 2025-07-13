import os
import sys
import time

import pytest

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from cursor_automation import CursorAutomation


class TestBasicFunctionality:
    """Basic functionality tests for Cursor AppImage"""

    def test_app_launch_and_close(self, cursor_app):
        """Test that app can launch and close properly"""
        # Test that app is available
        assert cursor_app.window is not None, "Window should be available"

        # Test window properties
        window_info = cursor_app.get_window_info()
        assert (
            window_info.get("title", "").lower() == "cursor"
        ), "Window title should be 'Cursor'"
        assert window_info.get("width", 0) > 0, "Window should have positive width"
        assert window_info.get("height", 0) > 0, "Window should have positive height"

    def test_window_focus(self, cursor_app):
        """Test window focusing"""
        assert cursor_app.focus_window(), "Should be able to focus window"

        # Wait a bit and check if window is still available
        time.sleep(1)
        window_info = cursor_app.get_window_info()
        assert window_info, "Window info should be available after focus"

    def test_screenshot_functionality(self, cursor_app):
        """Test screenshot taking"""
        screenshot_path = cursor_app.take_screenshot("test_screenshot.png")
        assert os.path.exists(screenshot_path), "Screenshot should be created"

        # Check file size (should be reasonable)
        file_size = os.path.getsize(screenshot_path)
        assert file_size > 1000, "Screenshot should have reasonable file size"

    def test_keyboard_input(self, cursor_app):
        """Test basic keyboard input"""
        # Focus window first
        cursor_app.focus_window()

        # Try to open command palette
        cursor_app.key_combo("ctrl", "shift", "p")
        time.sleep(1)

        # Take screenshot to verify command palette opened
        screenshot_path = cursor_app.take_screenshot("command_palette.png")
        assert os.path.exists(screenshot_path), "Should capture command palette"

        # Press escape to close
        cursor_app.key_combo("escape")
        time.sleep(1)

    def test_basic_text_input(self, cursor_app):
        """Test basic text input"""
        cursor_app.focus_window()

        # Try to create new file
        cursor_app.key_combo("ctrl", "n")
        time.sleep(1)

        # Type some text
        test_text = "// This is a test file\nconsole.log('Hello World');"
        cursor_app.type_text(test_text)
        time.sleep(1)

        # Take screenshot
        screenshot_path = cursor_app.take_screenshot("text_input.png")
        assert os.path.exists(screenshot_path), "Should capture text input"

    def test_file_operations(self, cursor_app):
        """Test basic file operations"""
        cursor_app.focus_window()

        # Try to open a file
        cursor_app.key_combo("ctrl", "o")
        time.sleep(2)

        # Take screenshot of file dialog
        screenshot_path = cursor_app.take_screenshot("file_dialog.png")
        assert os.path.exists(screenshot_path), "Should capture file dialog"

        # Press escape to close dialog
        cursor_app.key_combo("escape")
        time.sleep(1)

    def test_menu_navigation(self, cursor_app):
        """Test menu navigation"""
        cursor_app.focus_window()

        # Try to access File menu
        cursor_app.key_combo("alt", "f")
        time.sleep(1)

        # Take screenshot
        screenshot_path = cursor_app.take_screenshot("file_menu.png")
        assert os.path.exists(screenshot_path), "Should capture file menu"

        # Press escape to close menu
        cursor_app.key_combo("escape")
        time.sleep(1)

    def test_performance_metrics(self, cursor_app):
        """Test performance metrics collection"""
        # Get initial memory usage
        initial_memory = cursor_app.get_memory_usage()
        assert initial_memory, "Should get memory usage info"
        assert "memory_percent" in initial_memory, "Should have memory percentage"

        # Perform some actions to increase memory usage
        cursor_app.focus_window()

        # Open multiple files
        for i in range(3):
            cursor_app.key_combo("ctrl", "n")
            time.sleep(0.5)
            cursor_app.type_text(f"// File {i}\nconsole.log('Test {i}');")
            time.sleep(0.5)

        # Get memory usage after actions
        final_memory = cursor_app.get_memory_usage()
        assert final_memory, "Should get final memory usage"

        # Memory might increase (not guaranteed, but check structure)
        assert "memory_info" in final_memory, "Should have memory info details"
        assert "cpu_percent" in final_memory, "Should have CPU percentage"
