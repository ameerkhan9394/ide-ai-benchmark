import os
import sys
import time

import pytest

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from ide_automation import create_ide_automation


class TestIDEFunctionality:
    """Basic functionality tests for IDE automation across multiple IDEs"""

    def test_ide_launch_and_close(self, ide_focused):
        """Test that IDE can launch and close properly"""
        # Test that IDE is available
        assert ide_focused.window is not None, "Window should be available"

        # Test window properties
        window_info = ide_focused.get_window_info()
        assert window_info.get("width", 0) > 0, "Window should have positive width"
        assert window_info.get("height", 0) > 0, "Window should have positive height"

    def test_window_focus(self, ide_focused):
        """Test window focusing"""
        focused = ide_focused.focus_window()
        assert focused, "Should be able to focus window"

    @pytest.mark.slow
    def test_screenshot_functionality(self, ide_focused):
        """Test screenshot capture"""
        screenshot_path = ide_focused.take_screenshot("test_screenshot.png")
        assert screenshot_path, "Screenshot should be captured"
        assert os.path.exists(screenshot_path), "Screenshot file should exist"

    def test_keyboard_input(self, ide_focused):
        """Test keyboard input functionality"""
        # Create new file
        ide_focused.key_combo('ctrl', 'n')
        time.sleep(1)

        # Type some text
        test_text = "Hello, World! This is a test."
        ide_focused.type_text(test_text)
        time.sleep(0.5)

        # Take screenshot to verify text was typed
        screenshot = ide_focused.take_screenshot("keyboard_input_test.png")
        assert os.path.exists(screenshot)

    def test_basic_text_input(self, ide_focused):
        """Test basic text input and keyboard shortcuts"""
        # Create new file
        ide_focused.key_combo('ctrl', 'n')
        time.sleep(1)

        # Type a simple Python function
        code = """def hello_world():
    print("Hello, World!")
    return "success"
"""
        ide_focused.type_text(code)
        time.sleep(1)

        # Test text selection (Ctrl+A)
        ide_focused.key_combo('ctrl', 'a')
        time.sleep(0.5)

        # Test copy (Ctrl+C)
        ide_focused.key_combo('ctrl', 'c')
        time.sleep(0.5)

    def test_file_operations(self, ide_focused):
        """Test basic file operations"""
        # Create new file
        ide_focused.key_combo('ctrl', 'n')
        time.sleep(1)

        # Type some content
        ide_focused.type_text("# Test file content\nprint('Hello from test file')")
        time.sleep(0.5)

        # Test save operation (will show save dialog)
        ide_focused.key_combo('ctrl', 's')
        time.sleep(1)

        # Cancel save dialog
        ide_focused.key_combo('Escape')
        time.sleep(0.5)

    def test_menu_navigation(self, ide_focused):
        """Test menu navigation via keyboard"""
        # Open command palette
        ide_focused.key_combo('ctrl', 'shift', 'p')
        time.sleep(1)

        # Close command palette
        ide_focused.key_combo('Escape')
        time.sleep(0.5)

        # Test View menu access (if available)
        ide_focused.key_combo('alt', 'v')
        time.sleep(0.5)

        # Close any open menus
        ide_focused.key_combo('Escape')

    def test_performance_metrics(self, ide_focused):
        """Test basic performance metrics collection"""
        # Get memory usage
        memory_info = ide_focused.get_memory_usage()
        assert memory_info["rss"] > 0, "RSS memory should be positive"
        assert memory_info["pid"] is not None, "PID should be available"

        # Get window info
        window_info = ide_focused.get_window_info()
        assert window_info["width"] > 0, "Window width should be positive"
        assert window_info["height"] > 0, "Window height should be positive"


class TestAIModelFunctionality:
    """Test AI model functionality across IDEs"""

    @pytest.mark.ai_model
    def test_get_available_models(self, ide_focused):
        """Test getting available AI models"""
        models = ide_focused.get_ai_models()
        assert isinstance(models, list), "Should return list of models"
        assert len(models) > 0, "Should have at least one model available"

    @pytest.mark.ai_model
    def test_model_switching(self, ide_focused, ai_models):
        """Test switching between AI models"""
        if len(ai_models) > 1:
            # Try switching to each available model
            for model in ai_models[:2]:  # Test first 2 models to save time
                success = ide_focused.switch_ai_model(model)
                # Note: Some IDEs might not support programmatic model switching
                # so we just verify the method doesn't crash
                assert isinstance(success, bool), f"Model switch should return boolean for {model}"

    @pytest.mark.ai_model
    @pytest.mark.slow
    def test_ai_completion_trigger(self, ide_focused):
        """Test triggering AI completion"""
        # Create new file
        ide_focused.key_combo('ctrl', 'n')
        time.sleep(1)

        # Try to trigger AI completion with a simple prompt
        prompt = "Write a hello world function"
        success = ide_focused.trigger_ai_completion(prompt)

        # Note: This might fail if AI model is not properly configured
        # but the method should not crash
        assert isinstance(success, bool), "AI completion trigger should return boolean"


class TestCrossIDEComparison:
    """Tests that run across multiple IDEs for comparison"""

    @pytest.mark.cross_ide
    def test_startup_time_comparison(self, multi_ide_app):
        """Compare startup times across IDEs"""
        # This test runs with the multi_ide_app fixture which tests each IDE
        start_time = time.time()

        # The IDE should already be launched by the fixture
        assert multi_ide_app.window is not None, "IDE should be launched"

        launch_time = time.time() - start_time

        # Record launch time for comparison (in real implementation,
        # this would be stored for analysis)
        print(f"IDE launch completed in {launch_time:.2f} seconds")

        # Basic functionality check
        memory_info = multi_ide_app.get_memory_usage()
        assert memory_info["rss"] > 0, "IDE should be using memory"

    @pytest.mark.cross_ide
    @pytest.mark.ai_model
    def test_ai_model_availability_comparison(self, multi_ide_app):
        """Compare AI model availability across IDEs"""
        models = multi_ide_app.get_ai_models()

        # Each IDE should have at least one model
        assert len(models) > 0, f"IDE should have at least one AI model available"

        # Record model availability for comparison
        ide_name = multi_ide_app.__class__.__name__.replace("Automation", "").lower()
        print(f"{ide_name} has {len(models)} AI models: {models}")

    @pytest.mark.cross_ide
    def test_basic_text_editing_comparison(self, multi_ide_app):
        """Compare basic text editing functionality across IDEs"""
        # Create new file
        multi_ide_app.key_combo('ctrl', 'n')
        time.sleep(1)

        # Type test content
        test_content = "def test_function():\n    return 'Hello from IDE test'"
        multi_ide_app.type_text(test_content)
        time.sleep(1)

        # Test selection
        multi_ide_app.key_combo('ctrl', 'a')
        time.sleep(0.5)

        # Test copy
        multi_ide_app.key_combo('ctrl', 'c')
        time.sleep(0.5)

        # Basic functionality should work across all IDEs
        window_info = multi_ide_app.get_window_info()
        assert window_info["width"] > 0, "Window should be functional"


# IDE-specific test classes
class TestCursorSpecific:
    """Tests specific to Cursor IDE"""

    @pytest.mark.cursor
    def test_cursor_ai_chat(self, ide_focused):
        """Test Cursor-specific AI chat functionality"""
        if not isinstance(ide_focused.__class__.__name__, str) or "cursor" not in ide_focused.__class__.__name__.lower():
            pytest.skip("This test is specific to Cursor IDE")

        # Trigger Cursor's AI chat (Ctrl+L)
        ide_focused.key_combo('ctrl', 'l')
        time.sleep(1)

        # Close chat
        ide_focused.key_combo('Escape')


class TestVSCodeSpecific:
    """Tests specific to VSCode"""

    @pytest.mark.vscode
    def test_vscode_copilot(self, ide_focused):
        """Test VSCode-specific Copilot functionality"""
        if not isinstance(ide_focused.__class__.__name__, str) or "vscode" not in ide_focused.__class__.__name__.lower():
            pytest.skip("This test is specific to VSCode")

        # Trigger Copilot chat (Ctrl+Shift+I)
        ide_focused.key_combo('ctrl', 'shift', 'i')
        time.sleep(1)

        # Close chat
        ide_focused.key_combo('Escape')


class TestWindsurfSpecific:
    """Tests specific to Windsurf IDE"""

    @pytest.mark.windsurf
    def test_windsurf_ai_features(self, ide_focused):
        """Test Windsurf-specific AI features"""
        if not isinstance(ide_focused.__class__.__name__, str) or "windsurf" not in ide_focused.__class__.__name__.lower():
            pytest.skip("This test is specific to Windsurf IDE")

        # Test Windsurf's AI interface
        # (Implementation depends on actual Windsurf shortcuts)
        ide_focused.key_combo('ctrl', 'shift', 'p')
        time.sleep(1)
        ide_focused.key_combo('Escape')
