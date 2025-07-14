import logging
import os
import signal
import subprocess
import time
from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional, Tuple

import cv2
import numpy as np
import psutil
from PIL import Image
from screeninfo import get_monitors

# Handle X11 display connection more gracefully
XLIB_AVAILABLE = False
PYAUTOGUI_AVAILABLE = False

try:
    # Set display environment if not set (default to :99 for Docker, :0 for host)
    if "DISPLAY" not in os.environ:
        # Auto-detect if we're in Docker or host
        if os.path.exists("/home/testuser") or os.environ.get("CONTAINER", False):
            os.environ["DISPLAY"] = ":99"
        else:
            os.environ["DISPLAY"] = ":0"

    # Try to import X11 libraries (but don't test connection yet)
    import Xlib
    import Xlib.display
    import Xlib.protocol.event
    import Xlib.X

    XLIB_AVAILABLE = True
    print(f"X11 libraries imported successfully, DISPLAY={os.environ.get('DISPLAY')}")
except ImportError as e:
    print(f"X11 libraries not available: {e}")
    XLIB_AVAILABLE = False

# Import pyautogui after X11 setup
try:
    import pyautogui

    PYAUTOGUI_AVAILABLE = True
    print("PyAutoGUI imported successfully")
except Exception as e:  # Catch ALL exceptions, not just ImportError
    print(f"PyAutoGUI not available: {e}")
    PYAUTOGUI_AVAILABLE = False

    # Create dummy pyautogui module for fallback
    class DummyPyAutoGUI:
        PAUSE = 0.5

        @staticmethod
        def screenshot(*args, **kwargs):
            print("DummyPyAutoGUI.screenshot called")
            return None

        @staticmethod
        def click(*args, **kwargs):
            print("DummyPyAutoGUI.click called")
            return None

        @staticmethod
        def typewrite(*args, **kwargs):
            print("DummyPyAutoGUI.typewrite called")
            return None

        @staticmethod
        def hotkey(*args, **kwargs):
            print("DummyPyAutoGUI.hotkey called")
            return None

        @staticmethod
        def size():
            print("DummyPyAutoGUI.size called")
            return (1920, 1080)

    pyautogui = DummyPyAutoGUI()


class IDEAutomation(ABC):
    """Base class for IDE automation across different editors"""

    def __init__(self, app_path: str = None):
        self.app_path = app_path or self._get_default_app_path()
        self.process = None
        self.window = None
        self.pid = None

        # Setup logging
        logging.basicConfig(
            level=logging.INFO,
            format="%(asctime)s - %(levelname)s - %(message)s",
            handlers=[
                logging.FileHandler("ide_automation.log"),
                logging.StreamHandler(),
            ],
        )
        self.logger = logging.getLogger(__name__)

        # Validate environment
        self._validate_environment()

    @abstractmethod
    def _get_default_app_path(self) -> str:
        """Get the default application path for this IDE"""
        pass

    @abstractmethod
    def _get_process_name(self) -> str:
        """Get the process name to look for"""
        pass

    @abstractmethod
    def _get_window_title_pattern(self) -> str:
        """Get the window title pattern to match"""
        pass

    @abstractmethod
    def _get_launch_command(self) -> List[str]:
        """Get the command to launch the IDE"""
        pass

    @abstractmethod
    def get_ai_models(self) -> List[str]:
        """Get list of supported AI models for this IDE"""
        pass

    @abstractmethod
    def switch_ai_model(self, model_name: str) -> bool:
        """Switch to specified AI model"""
        pass

    @abstractmethod
    def trigger_ai_completion(self, prompt: str) -> bool:
        """Trigger AI completion with given prompt"""
        pass

    @abstractmethod
    def get_ai_response(self) -> str:
        """Get the AI response/completion"""
        pass

    def _validate_environment(self):
        """Validate that required dependencies are available"""
        if not PYAUTOGUI_AVAILABLE:
            self.logger.warning("PyAutoGUI not available, using fallback")
        if not XLIB_AVAILABLE:
            self.logger.warning("X11 libraries not available")

        # Test display connection
        display_available = self._test_display()
        if not display_available:
            self.logger.warning("Display connection failed, running in fallback mode")

    def _test_display(self) -> bool:
        """Test if display is available"""
        try:
            if XLIB_AVAILABLE:
                display = Xlib.display.Display()
                display.close()
                return True
        except Exception as e:
            self.logger.debug(f"Display test failed: {e}")
        return False

    def _test_pyautogui(self) -> bool:
        """Test PyAutoGUI functionality"""
        if not PYAUTOGUI_AVAILABLE:
            return False
        try:
            pyautogui.size()
            return True
        except Exception as e:
            self.logger.error(f"PyAutoGUI test failed: {e}")
            return False

    def _kill_existing_processes(self):
        """Kill existing processes of this IDE"""
        process_name = self._get_process_name()
        killed_processes = []

        for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
            try:
                # Check if process name matches
                if proc.info['name'] and process_name.lower() in proc.info['name'].lower():
                    self.logger.info(f"Killing existing {process_name} process: PID {proc.info['pid']}")
                    proc.kill()
                    killed_processes.append(proc.info['pid'])

                # Also check command line for AppImage paths
                elif proc.info['cmdline'] and any(process_name.lower() in str(cmd).lower() for cmd in proc.info['cmdline']):
                    self.logger.info(f"Killing existing {process_name} process via cmdline: PID {proc.info['pid']}")
                    proc.kill()
                    killed_processes.append(proc.info['pid'])

            except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                pass

        if killed_processes:
            time.sleep(2)  # Give processes time to terminate

        return killed_processes

    def _find_window_by_title(self, title_pattern: str) -> Optional[int]:
        """Find window by title pattern using X11"""
        if not XLIB_AVAILABLE:
            return None

        try:
            display = Xlib.display.Display()
            root = display.screen().root

            def get_window_name(window):
                try:
                    window_name = window.get_wm_name()
                    return window_name if window_name else ""
                except:
                    return ""

            def search_windows(window):
                window_name = get_window_name(window)
                if title_pattern.lower() in window_name.lower():
                    return window.id

                # Search child windows
                try:
                    children = window.query_tree().children
                    for child in children:
                        result = search_windows(child)
                        if result:
                            return result
                except:
                    pass

                return None

            window_id = search_windows(root)
            display.close()
            return window_id

        except Exception as e:
            self.logger.error(f"Error finding window: {e}")
            return None

    def _focus_window_x11(self, window_id: int) -> bool:
        """Focus window using X11"""
        if not XLIB_AVAILABLE:
            return False

        try:
            display = Xlib.display.Display()
            window = display.create_resource_object('window', window_id)
            window.set_input_focus(Xlib.X.RevertToParent, Xlib.X.CurrentTime)
            window.configure(stack_mode=Xlib.X.Above)
            display.sync()
            display.close()
            return True
        except Exception as e:
            self.logger.error(f"Error focusing window: {e}")
            return False

    def _get_window_info_x11(self, window_id: int) -> dict:
        """Get window information using X11"""
        if not XLIB_AVAILABLE:
            return {"width": 1920, "height": 1080, "x": 0, "y": 0, "title": "unknown"}

        try:
            display = Xlib.display.Display()
            window = display.create_resource_object('window', window_id)

            geometry = window.get_geometry()
            window_name = window.get_wm_name() or "unknown"

            info = {
                "width": geometry.width,
                "height": geometry.height,
                "x": geometry.x,
                "y": geometry.y,
                "title": window_name
            }

            display.close()
            return info

        except Exception as e:
            self.logger.error(f"Error getting window info: {e}")
            return {"width": 1920, "height": 1080, "x": 0, "y": 0, "title": "unknown"}

    def launch_app(self, timeout: int = 10) -> bool:
        """Launch the IDE application"""
        try:
            # Kill existing processes
            killed = self._kill_existing_processes()
            if killed:
                self.logger.info(f"Killed {len(killed)} existing processes")

            # Validate app path
            if not os.path.exists(self.app_path):
                self.logger.error(f"IDE application not found at: {self.app_path}")
                return False

            # Launch application
            cmd = self._get_launch_command()
            self.logger.info(f"Launching {self._get_process_name()} with command: {' '.join(cmd)}")

            self.process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                preexec_fn=os.setsid
            )

            self.pid = self.process.pid
            self.logger.info(f"{self._get_process_name()} launched with PID: {self.pid}")

            # Wait for window to appear
            title_pattern = self._get_window_title_pattern()
            start_time = time.time()

            while time.time() - start_time < timeout:
                self.window = self._find_window_by_title(title_pattern)
                if self.window:
                    self.logger.info(f"Found {self._get_process_name()} window: {self.window}")
                    time.sleep(1)  # Give window time to fully load
                    return True
                time.sleep(0.5)

            self.logger.error(f"Timeout waiting for {self._get_process_name()} window")
            return False

        except Exception as e:
            self.logger.error(f"Failed to launch {self._get_process_name()}: {e}")
            return False

    def close_app(self) -> bool:
        """Close the IDE application"""
        try:
            if self.process:
                self.logger.info(f"Terminating {self._get_process_name()} process")

                try:
                    os.killpg(os.getpgid(self.process.pid), signal.SIGTERM)
                    time.sleep(2)

                    if self.process.poll() is None:
                        os.killpg(os.getpgid(self.process.pid), signal.SIGKILL)
                        time.sleep(1)

                except ProcessLookupError:
                    pass

                self.process = None
                self.pid = None
                self.window = None
                return True

        except Exception as e:
            self.logger.error(f"Error closing {self._get_process_name()}: {e}")

        # Fallback: kill any remaining processes
        killed = self._kill_existing_processes()
        return len(killed) > 0

    def focus_window(self) -> bool:
        """Focus the IDE window"""
        if not self.window:
            title_pattern = self._get_window_title_pattern()
            self.window = self._find_window_by_title(title_pattern)

        if self.window:
            return self._focus_window_x11(self.window)
        return False

    def take_screenshot(self, filename: str = None) -> str:
        """Take screenshot of current state"""
        if not filename:
            timestamp = int(time.time())
            filename = f"screenshot_{timestamp}.png"

        # Ensure screenshots directory exists
        screenshot_dir = "screenshots"
        os.makedirs(screenshot_dir, exist_ok=True)
        filepath = os.path.join(screenshot_dir, filename)

        try:
            screenshot = pyautogui.screenshot()
            screenshot.save(filepath)
            self.logger.info(f"Screenshot saved: {filepath}")
            return filepath
        except Exception as e:
            self.logger.error(f"Failed to take screenshot: {e}")
            return ""

    def find_image_on_screen(self, image_path: str, confidence: float = 0.8) -> Optional[Tuple[int, int]]:
        """Find image on screen using OpenCV template matching"""
        try:
            # Take screenshot
            screenshot = pyautogui.screenshot()
            screenshot_cv = cv2.cvtColor(np.array(screenshot), cv2.COLOR_RGB2BGR)

            # Load template
            if not os.path.exists(image_path):
                self.logger.error(f"Template image not found: {image_path}")
                return None

            template = cv2.imread(image_path)
            if template is None:
                self.logger.error(f"Could not load template image: {image_path}")
                return None

            # Perform template matching
            result = cv2.matchTemplate(screenshot_cv, template, cv2.TM_CCOEFF_NORMED)
            locations = np.where(result >= confidence)

            if locations[0].size > 0:
                # Get the best match
                max_loc = np.unravel_index(np.argmax(result), result.shape)
                center_x = max_loc[1] + template.shape[1] // 2
                center_y = max_loc[0] + template.shape[0] // 2

                self.logger.info(f"Found image at ({center_x}, {center_y}) with confidence {result[max_loc]:.3f}")
                return (center_x, center_y)

        except Exception as e:
            self.logger.error(f"Error in image detection: {e}")

        return None

    def click_image(self, image_path: str, confidence: float = 0.8) -> bool:
        """Find and click an image on screen"""
        location = self.find_image_on_screen(image_path, confidence)
        if location:
            try:
                pyautogui.click(location[0], location[1])
                self.logger.info(f"Clicked at {location}")
                return True
            except Exception as e:
                self.logger.error(f"Failed to click: {e}")
        return False

    def type_text(self, text: str, interval: float = 0.01) -> None:
        """Type text with specified interval"""
        try:
            pyautogui.typewrite(text, interval=interval)
        except Exception as e:
            self.logger.error(f"Failed to type text: {e}")

    def key_combo(self, *keys) -> None:
        """Execute key combination"""
        try:
            pyautogui.hotkey(*keys)
        except Exception as e:
            self.logger.error(f"Failed to execute key combo {keys}: {e}")

    def wait_for_image(self, image_path: str, timeout: int = 10, confidence: float = 0.8) -> bool:
        """Wait for image to appear on screen"""
        start_time = time.time()
        while time.time() - start_time < timeout:
            if self.find_image_on_screen(image_path, confidence):
                return True
            time.sleep(0.5)
        return False

    def get_window_info(self) -> dict:
        """Get window information"""
        if self.window:
            return self._get_window_info_x11(self.window)
        return {"width": 1920, "height": 1080, "x": 0, "y": 0, "title": "unknown"}

    def get_memory_usage(self) -> dict:
        """Get memory usage information"""
        try:
            if self.pid:
                process = psutil.Process(self.pid)
                memory_info = process.memory_info()
                return {
                    "rss": memory_info.rss,  # Resident Set Size
                    "vms": memory_info.vms,  # Virtual Memory Size
                    "percent": process.memory_percent(),
                    "pid": self.pid
                }
        except Exception as e:
            self.logger.error(f"Failed to get memory usage: {e}")

        return {"rss": 0, "vms": 0, "percent": 0.0, "pid": None}

    def create_test_image(self, region: Tuple[int, int, int, int], filename: str) -> str:
        """Create a test image from screen region"""
        x, y, width, height = region
        try:
            screenshot = pyautogui.screenshot(region=(x, y, width, height))

            # Ensure test_images directory exists
            test_images_dir = "test_images"
            os.makedirs(test_images_dir, exist_ok=True)
            filepath = os.path.join(test_images_dir, filename)

            screenshot.save(filepath)
            self.logger.info(f"Test image created: {filepath}")
            return filepath
        except Exception as e:
            self.logger.error(f"Failed to create test image: {e}")
            return ""


class CursorAutomation(IDEAutomation):
    """Automation for Cursor IDE"""

    def _get_default_app_path(self) -> str:
        """Get default Cursor app path"""
        paths = [
            os.environ.get("CURSOR_PATH"),
            "/opt/cursor/cursor",
            "./cursor.AppImage",
            "/usr/local/bin/cursor",
            "/usr/bin/cursor"
        ]

        for path in paths:
            if path and os.path.exists(path):
                return path

        return "./cursor.AppImage"  # Default fallback

    def _get_process_name(self) -> str:
        return "cursor"

    def _get_window_title_pattern(self) -> str:
        return "cursor"

    def _get_launch_command(self) -> List[str]:
        return [self.app_path, "--no-sandbox", "--disable-dev-shm-usage"]

    def get_ai_models(self) -> List[str]:
        return ["claude-3.5-sonnet", "gpt-4", "gpt-4-turbo", "claude-3-haiku"]

    def switch_ai_model(self, model_name: str) -> bool:
        """Switch AI model in Cursor"""
        try:
            # Open command palette
            self.key_combo('ctrl', 'shift', 'p')
            time.sleep(1)

            # Type model switch command
            self.type_text("Cursor: Switch Model")
            time.sleep(0.5)

            # Press Enter
            self.key_combo('Return')
            time.sleep(1)

            # Select model
            self.type_text(model_name)
            time.sleep(0.5)
            self.key_combo('Return')

            return True
        except Exception as e:
            self.logger.error(f"Failed to switch model to {model_name}: {e}")
            return False

    def trigger_ai_completion(self, prompt: str) -> bool:
        """Trigger AI completion with prompt"""
        try:
            # Open chat/composer
            self.key_combo('ctrl', 'l')
            time.sleep(1)

            # Type prompt
            self.type_text(prompt)
            time.sleep(0.5)

            # Submit
            self.key_combo('Return')
            time.sleep(2)  # Wait for AI response

            return True
        except Exception as e:
            self.logger.error(f"Failed to trigger AI completion: {e}")
            return False

    def get_ai_response(self) -> str:
        """Get AI response from Cursor"""
        # This would need to be implemented based on Cursor's UI
        # For now, return a placeholder
        return "AI response placeholder"


class WindsurfAutomation(IDEAutomation):
    """Automation for Windsurf IDE"""

    def _get_default_app_path(self) -> str:
        paths = [
            os.environ.get("WINDSURF_PATH"),
            "/opt/windsurf/windsurf",
            "./windsurf.AppImage",
            "/usr/local/bin/windsurf"
        ]

        for path in paths:
            if path and os.path.exists(path):
                return path

        return "./windsurf.AppImage"

    def _get_process_name(self) -> str:
        return "windsurf"

    def _get_window_title_pattern(self) -> str:
        return "windsurf"

    def _get_launch_command(self) -> List[str]:
        return [self.app_path, "--no-sandbox"]

    def get_ai_models(self) -> List[str]:
        return ["claude-3.5-sonnet", "gpt-4", "claude-3-haiku"]

    def switch_ai_model(self, model_name: str) -> bool:
        """Switch AI model in Windsurf"""
        # Implementation specific to Windsurf
        return True

    def trigger_ai_completion(self, prompt: str) -> bool:
        """Trigger AI completion in Windsurf"""
        # Implementation specific to Windsurf
        return True

    def get_ai_response(self) -> str:
        """Get AI response from Windsurf"""
        return "Windsurf AI response placeholder"


class VSCodeAutomation(IDEAutomation):
    """Automation for VSCode with GitHub Copilot"""

    def _get_default_app_path(self) -> str:
        paths = [
            os.environ.get("VSCODE_PATH"),
            "/usr/bin/code",
            "/opt/visual-studio-code/code",
            "/usr/local/bin/code"
        ]

        for path in paths:
            if path and os.path.exists(path):
                return path

        return "/usr/bin/code"

    def _get_process_name(self) -> str:
        return "code"

    def _get_window_title_pattern(self) -> str:
        return "Visual Studio Code"

    def _get_launch_command(self) -> List[str]:
        return [self.app_path, "--no-sandbox"]

    def get_ai_models(self) -> List[str]:
        return ["github-copilot"]

    def switch_ai_model(self, model_name: str) -> bool:
        """Switch AI model in VSCode (limited to Copilot)"""
        return model_name == "github-copilot"

    def trigger_ai_completion(self, prompt: str) -> bool:
        """Trigger Copilot completion in VSCode"""
        try:
            # Trigger Copilot chat
            self.key_combo('ctrl', 'shift', 'i')
            time.sleep(1)

            self.type_text(prompt)
            self.key_combo('Return')

            return True
        except Exception as e:
            self.logger.error(f"Failed to trigger Copilot: {e}")
            return False

    def get_ai_response(self) -> str:
        """Get Copilot response from VSCode"""
        return "Copilot response placeholder"


# Factory function to create IDE automation instances
def create_ide_automation(ide_name: str, app_path: str = None) -> IDEAutomation:
    """Factory function to create IDE automation instances"""
    ide_classes = {
        "cursor": CursorAutomation,
        "windsurf": WindsurfAutomation,
        "vscode": VSCodeAutomation,
    }

    ide_class = ide_classes.get(ide_name.lower())
    if not ide_class:
        raise ValueError(f"Unsupported IDE: {ide_name}")

    return ide_class(app_path)