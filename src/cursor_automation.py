import logging
import os
import signal
import subprocess
import time
from typing import List, Optional, Tuple

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
        FAILSAFE = True
        PAUSE = 0.5

        @staticmethod
        def screenshot(*args, **kwargs):
            from PIL import Image

            return Image.new("RGB", (1920, 1080), color="black")

        @staticmethod
        def click(*args, **kwargs):
            pass

        @staticmethod
        def typewrite(*args, **kwargs):
            pass

        @staticmethod
        def hotkey(*args, **kwargs):
            pass

        @staticmethod
        def size():
            return (1920, 1080)

    pyautogui = DummyPyAutoGUI()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler("cursor_automation.log", mode="a"),
    ],
)
logger = logging.getLogger(__name__)


class CursorAutomation:
    """Main automation class for testing Cursor AppImage"""

    def __init__(self, appimage_path: str | None):
        # Auto-detect AppImage path based on environment
        if appimage_path is None:
            # Check environment variable first (for Docker)
            appimage_path = os.environ.get("CURSOR_PATH")

            if not appimage_path:
                # Try common paths - prioritize local project file
                import getpass

                user = getpass.getuser()
                possible_paths = [
                    "./cursor.AppImage",  # Local project directory (HIGHEST PRIORITY)
                    "/home/testuser/cursor-benchmark/cursor.AppImage",  # Docker container project root
                    "/home/testuser/Applications/cursor.AppImage",  # Docker container
                    f"/home/{user}/Applications/cursor/cursor.AppImage",  # Host system (dynamic user)
                ]

                for path in possible_paths:
                    if os.path.exists(path):
                        appimage_path = path
                        break

                # For testing purposes, allow None AppImage path
                if not appimage_path:
                    logger.warning(
                        "Cursor AppImage not found in common paths. Checking additional locations..."
                    )
                    # Additional container paths to check
                    extra_paths = [
                        "/home/testuser/Applications/cursor.AppImage",  # Explicit container path
                        "/opt/cursor/cursor.AppImage",  # Alternative location
                        "/usr/local/bin/cursor.AppImage",  # System location
                    ]
                    for path in extra_paths:
                        logger.info(f"Checking path: {path}")
                        if os.path.exists(path):
                            appimage_path = path
                            logger.info(f"Found Cursor AppImage at: {path}")
                            break

                    if not appimage_path:
                        logger.error(
                            "Cursor AppImage not found anywhere. This will cause test failures."
                        )
                        appimage_path = "/fake/path"

        self.appimage_path = appimage_path
        self.process = None
        self.window = None
        self.window_id = None
        self.screenshots_dir = "screenshots"
        self.test_images_dir = "test_images"

        # Create directories
        os.makedirs(self.screenshots_dir, exist_ok=True)
        os.makedirs(self.test_images_dir, exist_ok=True)

        # Configure pyautogui if available
        if PYAUTOGUI_AVAILABLE:
            try:
                pyautogui.FAILSAFE = True
                pyautogui.PAUSE = 0.5
                logger.info("PyAutoGUI configured successfully")

                # Test pyautogui when actually needed, not during init
                self._pyautogui_tested = False
            except Exception as e:
                logger.warning(f"PyAutoGUI configuration failed: {e}")
        else:
            logger.info("Using dummy PyAutoGUI implementation")
            self._pyautogui_tested = True  # Skip testing for dummy

        # Get monitor info
        try:
            self.monitors = get_monitors()
            self.primary_monitor = self.monitors[0]
            logger.info(
                f"Primary monitor: {self.primary_monitor.width}x{self.primary_monitor.height}"
            )
        except Exception as e:
            logger.warning(f"Could not get monitor info (no display available): {e}")

            # Provide fallback monitor info
            class FakeMonitor:
                width = 1920
                height = 1080
                x = 0
                y = 0

            self.primary_monitor = FakeMonitor()
            self.monitors = [self.primary_monitor]
            logger.info(
                f"Using fallback monitor: {self.primary_monitor.width}x{self.primary_monitor.height}"
            )

        logger.info(f"Initialized CursorAutomation with AppImage: {appimage_path}")

        # Initialize X11 display lazily (will be connected when needed)
        self.display = None
        if XLIB_AVAILABLE:
            logger.info(
                "X11 libraries available - display will be connected when needed"
            )
        else:
            logger.warning(
                "X11 libraries not available - window operations will be limited"
            )

    def _test_pyautogui(self) -> bool:
        """Test PyAutoGUI functionality when needed"""
        if self._pyautogui_tested:
            return PYAUTOGUI_AVAILABLE

        if not PYAUTOGUI_AVAILABLE:
            return False

        try:
            # Test basic PyAutoGUI operations
            size = pyautogui.size()
            logger.info(f"PyAutoGUI working - screen size: {size}")
            self._pyautogui_tested = True
            return True
        except Exception as e:
            logger.warning(f"PyAutoGUI test failed: {e}")
            self._pyautogui_tested = True  # Don't test again
            return False

    def _kill_existing_cursor_processes(self):
        """Kill any existing Cursor processes to prevent conflicts"""
        logger.info("Checking for existing Cursor processes...")

        killed_count = 0
        for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
            try:
                # Skip system-critical processes (PID 1, 2, etc.)
                if proc.pid <= 10:
                    continue

                # Check for Cursor-specific process indicators
                name = proc.name().lower() if proc.name() else ""
                cmdline = " ".join(proc.cmdline()) if proc.cmdline() else ""

                # More specific Cursor process detection
                is_cursor_process = False

                # Look for actual Cursor binary names
                if any(cursor_name in name for cursor_name in ['cursor', 'cursor-appimage']):
                    is_cursor_process = True

                # Look for Cursor AppImage in command line (more specific)
                if 'cursor.appimage' in cmdline.lower() and not cmdline.startswith('/bin/'):
                    is_cursor_process = True

                # Look for Cursor executable paths
                if any(path in cmdline.lower() for path in ['/opt/cursor/', '/applications/cursor', 'cursor.app']):
                    is_cursor_process = True

                if is_cursor_process:
                    logger.info(f"Found Cursor process: PID {proc.pid}, name: {name}, cmd: {cmdline[:100]}...")
                    try:
                        proc.terminate()
                        proc.wait(timeout=3)
                        killed_count += 1
                        logger.info(f"Terminated Cursor process: PID {proc.pid}")
                    except psutil.TimeoutExpired:
                        logger.warning(f"Force killing Cursor process: PID {proc.pid}")
                        proc.kill()
                        killed_count += 1
                    except psutil.AccessDenied:
                        logger.warning(f"Access denied when trying to kill process: PID {proc.pid}")
                    except psutil.NoSuchProcess:
                        logger.debug(f"Process already gone: PID {proc.pid}")

            except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                continue

        if killed_count > 0:
            logger.info(f"Killed {killed_count} existing Cursor process(es)")
        else:
            logger.info("No existing Cursor processes found")

        # Wait a moment for processes to fully terminate
        time.sleep(1)

    def _find_window_by_title(self, title: str) -> Optional[int]:
        """Find window by title using X11 (Linux)"""
        if not XLIB_AVAILABLE:
            logger.warning("X11 libraries not available for window finding")
            return None

        # Try to establish/reconnect to display
        if not self.display:
            try:
                logger.info(f"Connecting to X11 display: {os.environ.get('DISPLAY')}")
                self.display = Xlib.display.Display()
                logger.info("X11 display connection established")
            except Exception as e:
                logger.error(f"Failed to connect to X11 display: {e}")
                return None

        try:
            # Test display connection
            self.display.sync()
            root = self.display.screen().root

            def get_window_name(window):
                try:
                    return window.get_wm_name()
                except Exception as e:
                    logger.debug(f"Failed to get window name: {e}")
                    return None

            def search_windows(window):
                try:
                    window_name = get_window_name(window)
                    if window_name and title.lower() in window_name.lower():
                        logger.info(f"Found window: '{window_name}' (ID: {window.id})")
                        return window.id

                    # Search children
                    try:
                        children = window.query_tree().children
                        for child in children:
                            result = search_windows(child)
                            if result:
                                return result
                    except Exception as e:
                        logger.debug(f"Error querying window children: {e}")
                        pass

                    return None
                except Exception as e:
                    logger.debug(f"Error searching window: {e}")
                    return None

            return search_windows(root)

        except Exception as e:
            logger.error(f"Error finding window, X11 connection may be lost: {e}")
            # Try to reset display connection
            try:
                self.display.close()
            except:
                pass
            self.display = None
            return None

    def _focus_window_x11(self, window_id: int) -> bool:
        """Focus window using X11 (Linux)"""
        if not XLIB_AVAILABLE or not self.display:
            logger.warning("X11 not available for window focusing")
            return False

        try:
            window = self.display.create_resource_object("window", window_id)
            window.set_input_focus(Xlib.X.RevertToParent, Xlib.X.CurrentTime)
            window.configure(stack_mode=Xlib.X.Above)
            self.display.sync()
            logger.info(f"Successfully focused window ID: {window_id}")
            return True
        except Exception as e:
            logger.error(f"Error focusing window: {e}")
            return False

    def _get_window_info_x11(self, window_id: int) -> dict:
        """Get window info using X11 (Linux)"""
        if not XLIB_AVAILABLE or not self.display:
            logger.warning("X11 not available for window info")
            return {}

        try:
            window = self.display.create_resource_object("window", window_id)
            geom = window.get_geometry()
            attrs = window.get_attributes()

            info = {
                "title": window.get_wm_name() or "",
                "left": geom.x,
                "top": geom.y,
                "width": geom.width,
                "height": geom.height,
                "isMaximized": False,  # Would need more complex detection
                "isMinimized": attrs.map_state != Xlib.X.IsViewable,
            }
            logger.debug(f"Window info: {info}")
            return info
        except Exception as e:
            logger.error(f"Error getting window info: {e}")
            return {}

    def launch_app(self, timeout: int = 10) -> bool:
        """Launch Cursor AppImage and wait for it to be ready"""
        logger.info(f"Launching Cursor AppImage with timeout: {timeout}s")

        # Verify AppImage exists and is executable
        if not os.path.exists(self.appimage_path):
            logger.error(f"Cursor AppImage not found at: {self.appimage_path}")
            return False

        # Check if we have an extracted version (for containers without FUSE)
        extracted_binary = None
        if "/Applications/cursor.AppImage" in self.appimage_path:
            # Try to find extracted version
            base_dir = os.path.dirname(self.appimage_path)
            potential_extracted = os.path.join(base_dir, "cursor")
            if os.path.exists(potential_extracted):
                extracted_binary = potential_extracted
                logger.info(f"Found extracted Cursor binary: {extracted_binary}")

        # Use extracted binary if available, otherwise use AppImage
        binary_to_run = extracted_binary if extracted_binary else self.appimage_path

        if not os.access(binary_to_run, os.X_OK):
            logger.warning(f"Binary not executable, attempting to make executable: {binary_to_run}")
            try:
                os.chmod(binary_to_run, 0o755)
                logger.info("Successfully made binary executable")
            except PermissionError:
                logger.warning("Cannot make binary executable (read-only filesystem), trying anyway...")

        # Kill existing processes first
        self._kill_existing_cursor_processes()

        try:
            # Launch the binary
            logger.info(f"Starting process: {binary_to_run}")
            self.process = subprocess.Popen(
                [binary_to_run, "--no-sandbox"],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                preexec_fn=os.setsid,
            )

            logger.info(f"Process started with PID: {self.process.pid}")

            # Wait for window to appear
            start_time = time.time()
            attempt = 0
            while time.time() - start_time < timeout:
                attempt += 1
                logger.info(f"Looking for Cursor window (attempt {attempt})...")

                window_id = self._find_window_by_title("Cursor")
                if window_id:
                    self.window_id = window_id
                    self.window = {"id": window_id}  # Simple compatibility object
                    logger.info(f"Found Cursor window! ID: {window_id}")

                    # Wait a bit more for full load
                    logger.info("Waiting for application to fully load...")
                    time.sleep(2)

                    # Verify window is still there
                    if self._find_window_by_title("Cursor"):
                        logger.info("Cursor launched successfully!")
                        return True
                    else:
                        logger.warning("Window disappeared after initial detection")

                time.sleep(0.5)

            logger.error(f"Failed to find Cursor window within {timeout}s")
            return False

        except Exception as e:
            logger.error(f"Failed to launch app: {e}")
            return False

    def close_app(self) -> bool:
        """Close Cursor app properly"""
        logger.info("Closing Cursor application...")

        success = True

        # Try graceful shutdown first
        if self.process:
            try:
                logger.info("Attempting graceful shutdown...")

                # Focus window and try Ctrl+Q
                if self.window_id:
                    self._focus_window_x11(self.window_id)
                    time.sleep(0.5)
                    self.key_combo("ctrl", "q")
                    time.sleep(2)

                # Check if process is still running
                if self.process.poll() is None:
                    logger.info("Sending SIGTERM to process...")
                    self.process.terminate()

                    # Wait for termination
                    try:
                        self.process.wait(timeout=5)
                        logger.info("Process terminated gracefully")
                    except subprocess.TimeoutExpired:
                        logger.warning(
                            "Process didn't terminate gracefully, force killing..."
                        )
                        self.process.kill()
                        try:
                            self.process.wait(timeout=3)
                            logger.info("Process force killed")
                        except subprocess.TimeoutExpired:
                            logger.error("Failed to kill process")
                            success = False
                else:
                    logger.info("Process already terminated")

            except Exception as e:
                logger.error(f"Error during graceful shutdown: {e}")
                success = False

        # Kill any remaining Cursor processes
        self._kill_existing_cursor_processes()

        # Reset state
        self.process = None
        self.window = None
        self.window_id = None

        logger.info("App closure completed")
        return success

    def focus_window(self) -> bool:
        """Focus the Cursor window"""
        logger.info("Focusing Cursor window...")

        try:
            if self.window_id:
                success = self._focus_window_x11(self.window_id)
                if success:
                    time.sleep(0.5)
                    logger.info("Window focused successfully")
                    return True
                else:
                    logger.warning("Failed to focus window")
            else:
                logger.warning("No window ID available")
            return False
        except Exception as e:
            logger.error(f"Failed to focus window: {e}")
            return False

    def take_screenshot(self, filename: str = None) -> str:
        """Take a screenshot"""
        if filename is None:
            filename = f"screenshot_{int(time.time())}.png"

        filepath = os.path.join(self.screenshots_dir, filename)
        logger.info(f"Taking screenshot: {filepath}")

        try:
            if not self._test_pyautogui():
                logger.error("PyAutoGUI not available for screenshot")
                return ""

            screenshot = pyautogui.screenshot()
            screenshot.save(filepath)
            logger.info(f"Screenshot saved: {filepath}")
            return filepath
        except Exception as e:
            logger.error(f"Failed to take screenshot: {e}")
            return ""

    def find_image_on_screen(
        self, image_path: str, confidence: float = 0.8
    ) -> Optional[Tuple[int, int]]:
        """Find an image on screen using template matching"""
        logger.info(f"Searching for image: {image_path} (confidence: {confidence})")

        try:
            if not PYAUTOGUI_AVAILABLE:
                logger.error("PyAutoGUI not available for image search")
                return None

            # Take screenshot
            screenshot = pyautogui.screenshot()
            screenshot_np = np.array(screenshot)
            screenshot_cv = cv2.cvtColor(screenshot_np, cv2.COLOR_RGB2BGR)

            # Load template
            template = cv2.imread(image_path, cv2.IMREAD_COLOR)
            if template is None:
                logger.error(f"Could not load template image: {image_path}")
                return None

            # Template matching
            result = cv2.matchTemplate(screenshot_cv, template, cv2.TM_CCOEFF_NORMED)
            min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(result)

            logger.info(
                f"Template matching result: max_val={max_val}, confidence={confidence}"
            )

            if max_val >= confidence:
                # Get center of the matched region
                template_h, template_w = template.shape[:2]
                center_x = max_loc[0] + template_w // 2
                center_y = max_loc[1] + template_h // 2

                logger.info(f"Image found at: ({center_x}, {center_y})")
                return (center_x, center_y)
            else:
                logger.info("Image not found with required confidence")
                return None

        except Exception as e:
            logger.error(f"Error in image search: {e}")
            return None

    def click_image(self, image_path: str, confidence: float = 0.8) -> bool:
        """Click on an image found on screen"""
        logger.info(f"Attempting to click on image: {image_path}")

        position = self.find_image_on_screen(image_path, confidence)
        if position:
            if not PYAUTOGUI_AVAILABLE:
                logger.error("PyAutoGUI not available for clicking")
                return False

            pyautogui.click(position[0], position[1])
            logger.info(f"Clicked at position: {position}")
            return True
        else:
            logger.warning(f"Could not find image to click: {image_path}")
            return False

    def type_text(self, text: str, interval: float = 0.01) -> None:
        """Type text with specified interval"""
        logger.info(f"Typing text: '{text[:50]}{'...' if len(text) > 50 else ''}'")

        if not self._test_pyautogui():
            logger.error("PyAutoGUI not available for typing")
            return

        pyautogui.typewrite(text, interval=interval)

    def key_combo(self, *keys) -> None:
        """Press a key combination"""
        logger.info(f"Pressing key combination: {'+'.join(keys)}")

        if not self._test_pyautogui():
            logger.error("PyAutoGUI not available for key combinations")
            return

        pyautogui.hotkey(*keys)

    def wait_for_image(
        self, image_path: str, timeout: int = 10, confidence: float = 0.8
    ) -> bool:
        """Wait for an image to appear on screen"""
        logger.info(f"Waiting for image: {image_path} (timeout: {timeout}s)")

        start_time = time.time()
        while time.time() - start_time < timeout:
            if self.find_image_on_screen(image_path, confidence):
                logger.info(f"Image appeared after {time.time() - start_time:.2f}s")
                return True
            time.sleep(0.5)

        logger.warning(f"Image did not appear within {timeout}s")
        return False

    def get_window_info(self) -> dict:
        """Get current window information"""
        logger.debug("Getting window info...")

        if self.window_id:
            return self._get_window_info_x11(self.window_id)
        else:
            logger.warning("No window ID available")
            return {}

    def get_memory_usage(self) -> dict:
        """Get memory usage of the Cursor process"""
        logger.debug("Getting memory usage...")

        if self.process:
            try:
                proc = psutil.Process(self.process.pid)
                usage = {
                    "memory_percent": proc.memory_percent(),
                    "memory_info": proc.memory_info()._asdict(),
                    "cpu_percent": proc.cpu_percent(),
                }
                logger.debug(f"Memory usage: {usage['memory_percent']:.2f}%")
                return usage
            except (psutil.NoSuchProcess, psutil.AccessDenied) as e:
                logger.warning(f"Could not get memory usage: {e}")
        else:
            logger.warning("No process available for memory usage")
        return {}

    def create_test_image(
        self, region: Tuple[int, int, int, int], filename: str
    ) -> str:
        """Create a test image from a screen region"""
        logger.info(f"Creating test image: {filename} from region: {region}")

        try:
            if not PYAUTOGUI_AVAILABLE:
                logger.error("PyAutoGUI not available for creating test image")
                return ""

            screenshot = pyautogui.screenshot(region=region)
            filepath = os.path.join(self.test_images_dir, filename)
            screenshot.save(filepath)
            logger.info(f"Test image saved: {filepath}")
            return filepath
        except Exception as e:
            logger.error(f"Failed to create test image: {e}")
            return ""
