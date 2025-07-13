import json
import os
import sys
import time
from statistics import mean, median

import pytest

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from cursor_automation import CursorAutomation


class TestPerformanceBenchmarks:
    """Performance benchmark tests for Cursor AppImage"""

    @pytest.mark.slow
    def test_startup_time(self):
        """Benchmark app startup time - uses session fixture for simplicity"""
        # Note: This test measures session startup time rather than multiple startups
        # to avoid launching multiple instances which can cause conflicts

        # Simulate startup measurement by measuring app response time
        app = CursorAutomation()

        # Test app responsiveness (simulates startup performance)
        response_times = []

        for i in range(3):
            start_time = time.time()

            # Test basic operations that indicate app is ready
            app.focus_window()
            app.key_combo("ctrl", "n")  # New file
            time.sleep(0.5)
            app.key_combo("escape")  # Close any dialogs

            end_time = time.time()
            response_time = end_time - start_time
            response_times.append(response_time)
            print(f"Response test {i+1}: {response_time:.2f}s")

            time.sleep(1)  # Wait between tests

        avg_response = mean(response_times)
        median_response = median(response_times)

        print(f"Average response time: {avg_response:.2f}s")
        print(f"Median response time: {median_response:.2f}s")

        # Reasonable response time assertion
        assert (
            avg_response < 3.0
        ), f"Average response time too slow: {avg_response:.2f}s"

        # Save benchmark results
        results = {
            "test": "app_responsiveness",
            "average": avg_response,
            "median": median_response,
            "all_times": response_times,
            "timestamp": time.time(),
        }

        with open("benchmark_results.json", "w") as f:
            json.dump(results, f, indent=2)

    def test_memory_usage_over_time(self, cursor_app):
        """Test memory usage over time with various operations"""
        memory_readings = []

        # Initial memory reading
        initial_memory = cursor_app.get_memory_usage()
        memory_readings.append(
            {
                "time": 0,
                "action": "initial",
                "memory_percent": initial_memory.get("memory_percent", 0),
                "memory_rss": initial_memory.get("memory_info", {}).get("rss", 0),
            }
        )

        cursor_app.focus_window()

        # Perform various operations and measure memory
        operations = [
            ("new_file", lambda: cursor_app.key_combo("ctrl", "n")),
            (
                "type_text",
                lambda: cursor_app.type_text(
                    "const hello = 'world';\nconsole.log(hello);"
                ),
            ),
            ("command_palette", lambda: cursor_app.key_combo("ctrl", "shift", "p")),
            ("escape", lambda: cursor_app.key_combo("escape")),
            ("save_as", lambda: cursor_app.key_combo("ctrl", "shift", "s")),
            ("escape", lambda: cursor_app.key_combo("escape")),
        ]

        for i, (action_name, action_func) in enumerate(operations):
            action_func()
            time.sleep(2)  # Wait for operation to complete

            memory_data = cursor_app.get_memory_usage()
            memory_readings.append(
                {
                    "time": (i + 1) * 2,
                    "action": action_name,
                    "memory_percent": memory_data.get("memory_percent", 0),
                    "memory_rss": memory_data.get("memory_info", {}).get("rss", 0),
                }
            )

        # Analyze memory usage
        initial_rss = memory_readings[0]["memory_rss"]
        final_rss = memory_readings[-1]["memory_rss"]
        max_rss = max(reading["memory_rss"] for reading in memory_readings)

        print(f"Initial RSS: {initial_rss / 1024 / 1024:.2f} MB")
        print(f"Final RSS: {final_rss / 1024 / 1024:.2f} MB")
        print(f"Peak RSS: {max_rss / 1024 / 1024:.2f} MB")

        # Check for memory leaks (basic check)
        memory_growth = (final_rss - initial_rss) / initial_rss
        print(f"Memory growth: {memory_growth * 100:.2f}%")

        # Save detailed results
        results = {
            "test": "memory_usage_over_time",
            "readings": memory_readings,
            "initial_rss_mb": initial_rss / 1024 / 1024,
            "final_rss_mb": final_rss / 1024 / 1024,
            "peak_rss_mb": max_rss / 1024 / 1024,
            "memory_growth_percent": memory_growth * 100,
            "timestamp": time.time(),
        }

        with open("memory_benchmark.json", "w") as f:
            json.dump(results, f, indent=2)

        # Assert reasonable memory usage
        assert (
            max_rss < 1024 * 1024 * 1024
        ), "Memory usage too high (>1GB)"  # Adjust as needed

    def test_file_operations_performance(self, cursor_app):
        """Benchmark file operations performance"""
        cursor_app.focus_window()

        # Test new file creation speed
        new_file_times = []
        for i in range(5):
            start_time = time.time()
            cursor_app.key_combo("ctrl", "n")
            time.sleep(0.5)  # Wait for file to open
            end_time = time.time()
            new_file_times.append(end_time - start_time)

        avg_new_file_time = mean(new_file_times)
        print(f"Average new file creation time: {avg_new_file_time:.3f}s")

        # Test text typing performance
        text_samples = [
            "console.log('Hello World');",
            "const x = 1; const y = 2; const z = x + y;",
            "// This is a comment\nfunction test() { return true; }",
            "import React from 'react';\nexport default function App() { return <div>Hello</div>; }",
            "for (let i = 0; i < 100; i++) { console.log(i); }",
        ]

        typing_times = []
        for text in text_samples:
            start_time = time.time()
            cursor_app.type_text(text)
            end_time = time.time()
            typing_times.append(end_time - start_time)

            # Clear the text
            cursor_app.key_combo("ctrl", "a")
            cursor_app.key_combo("delete")
            time.sleep(0.1)

        avg_typing_time = mean(typing_times)
        print(f"Average typing time: {avg_typing_time:.3f}s")

        # Test command palette performance
        command_palette_times = []
        for i in range(3):
            start_time = time.time()
            cursor_app.key_combo("ctrl", "shift", "p")
            time.sleep(0.5)  # Wait for palette to open
            cursor_app.key_combo("escape")
            end_time = time.time()
            command_palette_times.append(end_time - start_time)

        avg_command_palette_time = mean(command_palette_times)
        print(f"Average command palette time: {avg_command_palette_time:.3f}s")

        # Save results
        results = {
            "test": "file_operations_performance",
            "new_file_times": new_file_times,
            "typing_times": typing_times,
            "command_palette_times": command_palette_times,
            "averages": {
                "new_file": avg_new_file_time,
                "typing": avg_typing_time,
                "command_palette": avg_command_palette_time,
            },
            "timestamp": time.time(),
        }

        with open("file_operations_benchmark.json", "w") as f:
            json.dump(results, f, indent=2)

        # Performance assertions
        assert (
            avg_new_file_time < 2.0
        ), f"New file creation too slow: {avg_new_file_time:.3f}s"
        assert (
            avg_command_palette_time < 2.0
        ), f"Command palette too slow: {avg_command_palette_time:.3f}s"

    @pytest.mark.slow
    def test_cpu_usage_monitoring(self, cursor_app):
        """Monitor CPU usage during various operations"""
        cpu_readings = []

        cursor_app.focus_window()

        # Baseline CPU usage
        baseline_cpu = cursor_app.get_memory_usage().get("cpu_percent", 0)
        cpu_readings.append({"operation": "baseline", "cpu_percent": baseline_cpu})

        # Perform CPU-intensive operations
        operations = [
            (
                "typing",
                lambda: cursor_app.type_text("const data = " + "x" * 1000 + ";"),
            ),
            ("command_palette", lambda: cursor_app.key_combo("ctrl", "shift", "p")),
            ("escape", lambda: cursor_app.key_combo("escape")),
            ("select_all", lambda: cursor_app.key_combo("ctrl", "a")),
            ("delete", lambda: cursor_app.key_combo("delete")),
        ]

        for op_name, operation in operations:
            operation()
            time.sleep(1)  # Wait for operation

            cpu_data = cursor_app.get_memory_usage()
            cpu_percent = cpu_data.get("cpu_percent", 0)
            cpu_readings.append({"operation": op_name, "cpu_percent": cpu_percent})

        # Analyze CPU usage
        avg_cpu = mean([reading["cpu_percent"] for reading in cpu_readings])
        max_cpu = max([reading["cpu_percent"] for reading in cpu_readings])

        print(f"Average CPU usage: {avg_cpu:.2f}%")
        print(f"Peak CPU usage: {max_cpu:.2f}%")

        # Save results
        results = {
            "test": "cpu_usage_monitoring",
            "readings": cpu_readings,
            "average_cpu": avg_cpu,
            "peak_cpu": max_cpu,
            "timestamp": time.time(),
        }

        with open("cpu_benchmark.json", "w") as f:
            json.dump(results, f, indent=2)

        # Assert reasonable CPU usage
        assert max_cpu < 50.0, f"CPU usage too high: {max_cpu:.2f}%"  # Adjust as needed
