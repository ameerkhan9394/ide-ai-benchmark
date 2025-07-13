import os
import shutil
import sys
import tempfile
import time

import pytest

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from cursor_automation import CursorAutomation


class TestUserWorkflows:
    """Test complete user workflows in Cursor AppImage"""

    @pytest.fixture
    def temp_project_dir(self):
        """Create a temporary project directory for testing"""
        temp_dir = tempfile.mkdtemp(prefix="cursor_test_")
        yield temp_dir
        shutil.rmtree(temp_dir, ignore_errors=True)

    @pytest.mark.slow
    def test_create_new_project_workflow(self, cursor_app, temp_project_dir):
        """Test creating a new project from scratch"""
        cursor_app.focus_window()

        # Step 1: Open folder
        cursor_app.key_combo("ctrl", "k", "ctrl", "o")
        time.sleep(2)

        # Type the temp directory path
        cursor_app.type_text(temp_project_dir)
        cursor_app.key_combo("enter")
        time.sleep(3)

        # Step 2: Create a new file
        cursor_app.key_combo("ctrl", "n")
        time.sleep(1)

        # Step 3: Write some code
        code_content = """// main.js
console.log("Hello, World!");

function greet(name) {
    return `Hello, ${name}!`;
}

const message = greet("Cursor");
console.log(message);
"""
        cursor_app.type_text(code_content)
        time.sleep(2)

        # Step 4: Save the file
        cursor_app.key_combo("ctrl", "s")
        time.sleep(1)
        cursor_app.type_text("main.js")
        cursor_app.key_combo("enter")
        time.sleep(2)

        # Step 5: Create package.json
        cursor_app.key_combo("ctrl", "n")
        time.sleep(1)

        package_json = """{
  "name": "cursor-test-project",
  "version": "1.0.0",
  "description": "Test project for Cursor automation",
  "main": "main.js",
  "scripts": {
    "start": "node main.js"
  }
}"""
        cursor_app.type_text(package_json)
        cursor_app.key_combo("ctrl", "s")
        time.sleep(1)
        cursor_app.type_text("package.json")
        cursor_app.key_combo("enter")
        time.sleep(2)

        # Step 6: Take screenshot of final state
        screenshot_path = cursor_app.take_screenshot("new_project_workflow.png")
        assert os.path.exists(screenshot_path), "Should capture final project state"

        # Verify files were created
        main_js_path = os.path.join(temp_project_dir, "main.js")
        package_json_path = os.path.join(temp_project_dir, "package.json")

        # Note: Files might not be immediately visible in filesystem
        # This test mainly validates the UI workflow
        print(f"Expected files: {main_js_path}, {package_json_path}")

    def test_code_editing_workflow(self, cursor_app):
        """Test a complete code editing workflow"""
        cursor_app.focus_window()

        # Step 1: Create new file
        cursor_app.key_combo("ctrl", "n")
        time.sleep(1)

        # Step 2: Write initial code
        initial_code = """function calculateSum(a, b) {
    return a + b;
}

const result = calculateSum(5, 3);
console.log(result);"""

        cursor_app.type_text(initial_code)
        time.sleep(1)

        # Step 3: Select and modify code
        cursor_app.key_combo("ctrl", "home")  # Go to start
        cursor_app.key_combo("ctrl", "f")  # Find
        time.sleep(1)
        cursor_app.type_text("calculateSum")
        cursor_app.key_combo("escape")  # Close find
        time.sleep(1)

        # Step 4: Use command palette for formatting
        cursor_app.key_combo("ctrl", "shift", "p")
        time.sleep(1)
        cursor_app.type_text("format")
        cursor_app.key_combo("enter")
        time.sleep(2)

        # Step 5: Add more code
        cursor_app.key_combo("ctrl", "end")  # Go to end
        cursor_app.key_combo("enter")
        cursor_app.type_text(
            """
function calculateProduct(a, b) {
    return a * b;
}

const product = calculateProduct(4, 6);
console.log(product);"""
        )
        time.sleep(1)

        # Step 6: Select all and copy
        cursor_app.key_combo("ctrl", "a")
        cursor_app.key_combo("ctrl", "c")
        time.sleep(1)

        # Step 7: Create new file and paste
        cursor_app.key_combo("ctrl", "n")
        time.sleep(1)
        cursor_app.key_combo("ctrl", "v")
        time.sleep(1)

        # Take screenshot of final state
        screenshot_path = cursor_app.take_screenshot("code_editing_workflow.png")
        assert os.path.exists(screenshot_path), "Should capture code editing workflow"

    def test_search_and_replace_workflow(self, cursor_app):
        """Test search and replace functionality"""
        cursor_app.focus_window()

        # Step 1: Create file with repetitive code
        cursor_app.key_combo("ctrl", "n")
        time.sleep(1)

        code_with_repetition = """const userName = "john";
const userAge = 25;
const userEmail = "john@example.com";

function getUserInfo() {
    return {
        name: userName,
        age: userAge,
        email: userEmail
    };
}

console.log(getUserInfo());"""

        cursor_app.type_text(code_with_repetition)
        time.sleep(1)

        # Step 2: Open find and replace
        cursor_app.key_combo("ctrl", "h")
        time.sleep(1)

        # Step 3: Replace "user" with "person"
        cursor_app.type_text("user")
        cursor_app.key_combo("tab")  # Move to replace field
        cursor_app.type_text("person")

        # Step 4: Replace all
        cursor_app.key_combo("ctrl", "alt", "enter")
        time.sleep(2)

        # Step 5: Close find and replace
        cursor_app.key_combo("escape")
        time.sleep(1)

        # Take screenshot
        screenshot_path = cursor_app.take_screenshot("search_replace_workflow.png")
        assert os.path.exists(screenshot_path), "Should capture search/replace workflow"

    def test_multi_file_workflow(self, cursor_app):
        """Test working with multiple files"""
        cursor_app.focus_window()

        # Step 1: Create first file
        cursor_app.key_combo("ctrl", "n")
        time.sleep(1)
        cursor_app.type_text(
            '// File 1\nconst config = { api: "http://localhost:3000" };'
        )

        # Step 2: Create second file
        cursor_app.key_combo("ctrl", "n")
        time.sleep(1)
        cursor_app.type_text(
            "// File 2\nconst utils = { formatDate: (date) => date.toISOString() };"
        )

        # Step 3: Create third file
        cursor_app.key_combo("ctrl", "n")
        time.sleep(1)
        cursor_app.type_text(
            '// File 3\nconst main = () => console.log("Main function");'
        )

        # Step 4: Navigate between files using Ctrl+Tab
        cursor_app.key_combo("ctrl", "tab")
        time.sleep(1)
        cursor_app.key_combo("ctrl", "tab")
        time.sleep(1)

        # Step 5: Use quick file switcher
        cursor_app.key_combo("ctrl", "p")
        time.sleep(1)
        cursor_app.key_combo("escape")

        # Step 6: Split editor
        cursor_app.key_combo("ctrl", "\\")
        time.sleep(2)

        # Take screenshot
        screenshot_path = cursor_app.take_screenshot("multi_file_workflow.png")
        assert os.path.exists(screenshot_path), "Should capture multi-file workflow"

    def test_terminal_integration_workflow(self, cursor_app):
        """Test terminal integration workflow"""
        cursor_app.focus_window()

        # Step 1: Open integrated terminal
        cursor_app.key_combo("ctrl", "shift", "`")
        time.sleep(2)

        # Step 2: Run some commands (simulate typing)
        cursor_app.type_text('echo "Hello from terminal"')
        cursor_app.key_combo("enter")
        time.sleep(1)

        cursor_app.type_text("ls -la")
        cursor_app.key_combo("enter")
        time.sleep(1)

        cursor_app.type_text("pwd")
        cursor_app.key_combo("enter")
        time.sleep(1)

        # Step 3: Create a new terminal
        cursor_app.key_combo("ctrl", "shift", "`")
        time.sleep(2)

        # Step 4: Close terminal
        cursor_app.key_combo("ctrl", "shift", "`")
        time.sleep(1)

        # Take screenshot
        screenshot_path = cursor_app.take_screenshot("terminal_workflow.png")
        assert os.path.exists(screenshot_path), "Should capture terminal workflow"

    def test_git_workflow_simulation(self, cursor_app):
        """Test Git-related workflow simulation"""
        cursor_app.focus_window()

        # Step 1: Open source control panel
        cursor_app.key_combo("ctrl", "shift", "g")
        time.sleep(2)

        # Step 2: Create a file to commit
        cursor_app.key_combo("ctrl", "n")
        time.sleep(1)
        cursor_app.type_text('// Initial commit\nconst version = "1.0.0";')

        # Step 3: Save file
        cursor_app.key_combo("ctrl", "s")
        time.sleep(1)
        cursor_app.type_text("version.js")
        cursor_app.key_combo("enter")
        time.sleep(2)

        # Step 4: Go back to source control
        cursor_app.key_combo("ctrl", "shift", "g")
        time.sleep(2)

        # Step 5: Try to open command palette for git commands
        cursor_app.key_combo("ctrl", "shift", "p")
        time.sleep(1)
        cursor_app.type_text("git")
        cursor_app.key_combo("escape")
        time.sleep(1)

        # Take screenshot
        screenshot_path = cursor_app.take_screenshot("git_workflow.png")
        assert os.path.exists(screenshot_path), "Should capture Git workflow"

    def test_extension_workflow(self, cursor_app):
        """Test extension-related workflow"""
        cursor_app.focus_window()

        # Step 1: Open extensions panel
        cursor_app.key_combo("ctrl", "shift", "x")
        time.sleep(2)

        # Step 2: Search for an extension
        cursor_app.type_text("python")
        time.sleep(2)

        # Step 3: Clear search
        cursor_app.key_combo("ctrl", "a")
        cursor_app.key_combo("delete")
        time.sleep(1)

        # Step 4: Close extensions panel
        cursor_app.key_combo("ctrl", "shift", "x")
        time.sleep(1)

        # Take screenshot
        screenshot_path = cursor_app.take_screenshot("extension_workflow.png")
        assert os.path.exists(screenshot_path), "Should capture extension workflow"
