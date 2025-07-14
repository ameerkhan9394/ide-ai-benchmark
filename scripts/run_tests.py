#!/usr/bin/env python3
"""
Multi-IDE AI Model Benchmark Test Runner
Provides various test execution options across different IDEs and AI models.
"""

import argparse
import json
import os
import subprocess
import sys
import time
from pathlib import Path
from typing import Any, Dict, List

# Supported IDEs and their default models
SUPPORTED_IDES = {
    "cursor": ["claude-3.5-sonnet", "gpt-4", "gpt-4-turbo"],
    "windsurf": ["claude-3.5-sonnet", "gpt-4", "gemini-pro"],
    "vscode": ["github-copilot"],
}

# Available test categories
TEST_CATEGORIES = {
    "basic": "tests/test_basic_functionality.py",
    "performance": "tests/test_performance_benchmarks.py",
    "workflows": "tests/test_user_workflows.py",
    "cross-ide": "tests/test_cross_ide_performance.py",
    "ai-models": "tests/test_ai_model_quality.py",
}


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
    os.makedirs("screenshots", exist_ok=True)
    os.makedirs("test_images", exist_ok=True)
    os.makedirs("reports", exist_ok=True)
    os.makedirs("results", exist_ok=True)

    print("Test environment setup completed")


def check_ide_availability(ide_name: str) -> bool:
    """Check if an IDE is available"""
    env_var = f"{ide_name.upper()}_PATH"
    ide_path = os.environ.get(env_var)

    if not ide_path:
        print(f"Warning: {env_var} not set")
        return False

    if not os.path.exists(ide_path):
        print(f"Warning: {ide_name} not found at {ide_path}")
        return False

    return True


def check_api_keys() -> Dict[str, bool]:
    """Check which AI model API keys are available"""
    api_keys = {
        "openai": bool(os.environ.get("OPENAI_API_KEY")),
        "anthropic": bool(os.environ.get("ANTHROPIC_API_KEY")),
        "google": bool(os.environ.get("GOOGLE_API_KEY")),
    }

    for provider, available in api_keys.items():
        status = "✓" if available else "✗"
        print(f"{status} {provider.title()} API key: {'Available' if available else 'Missing'}")

    return api_keys


def run_ide_tests(ide: str, models: List[str] = None, test_categories: List[str] = None):
    """Run tests for a specific IDE"""
    print(f"\n=== Running tests for {ide.upper()} IDE ===")

    if not check_ide_availability(ide):
        print(f"Skipping {ide} - not available")
        return False

    # Get models to test
    if not models:
        models = SUPPORTED_IDES.get(ide, [])

    # Get test categories to run
    if not test_categories:
        test_categories = ["basic"]

    success = True

    for category in test_categories:
        test_file = TEST_CATEGORIES.get(category, f"tests/test_{category}.py")

        if not os.path.exists(test_file):
            print(f"Warning: Test file {test_file} not found, skipping")
            continue

        print(f"\nRunning {category} tests for {ide}...")

        # Build pytest command
        cmd = [
            "python", "-m", "pytest",
            test_file,
            f"--ide={ide}",
            "--verbose",
            "--tb=short",
            f"--html=reports/{ide}_{category}_report.html",
            "--self-contained-html"
        ]

        # Add model-specific tests if models are specified
        if models and len(models) == 1:
            cmd.append(f"--model={models[0]}")

        # Run the test
        result = run_command(" ".join(cmd))
        if not result:
            print(f"Tests failed for {ide} {category}")
            success = False
        else:
            print(f"Tests passed for {ide} {category}")

    return success


def run_cross_ide_comparison(ides: List[str], models: List[str] = None):
    """Run cross-IDE comparison tests"""
    print(f"\n=== Running cross-IDE comparison tests ===")
    print(f"IDEs: {', '.join(ides)}")

    # Filter available IDEs
    available_ides = [ide for ide in ides if check_ide_availability(ide)]

    if len(available_ides) < 2:
        print("Error: Need at least 2 IDEs available for comparison")
        return False

    # Run cross-IDE tests
    cmd = [
        "python", "-m", "pytest",
        "tests/",
        "-m", "cross_ide",
        "--verbose",
        "--tb=short",
        "--html=reports/cross_ide_comparison.html",
        "--self-contained-html"
    ]

    return run_command(" ".join(cmd))


def run_performance_benchmarks(ides: List[str] = None, models: List[str] = None):
    """Run performance benchmarks across IDEs"""
    print(f"\n=== Running performance benchmarks ===")

    if not ides:
        ides = list(SUPPORTED_IDES.keys())

    results = {}

    for ide in ides:
        if not check_ide_availability(ide):
            continue

        print(f"\nBenchmarking {ide}...")

        # Run performance tests
        cmd = [
            "python", "-m", "pytest",
            "tests/test_performance_benchmarks.py",
            f"--ide={ide}",
            "--verbose",
            "--benchmark-json=results/benchmark_{ide}.json"
        ]

        start_time = time.time()
        success = run_command(" ".join(cmd))
        end_time = time.time()

        results[ide] = {
            "success": success,
            "duration": end_time - start_time,
            "timestamp": time.time()
        }

    # Save results
    with open("results/performance_comparison.json", "w") as f:
        json.dump(results, f, indent=2)

    return True


def run_ai_model_quality_tests(ides: List[str] = None, models: List[str] = None):
    """Run AI model quality tests"""
    print(f"\n=== Running AI model quality tests ===")

    if not ides:
        ides = list(SUPPORTED_IDES.keys())

    results = {}

    for ide in ides:
        if not check_ide_availability(ide):
            continue

        ide_models = models or SUPPORTED_IDES.get(ide, [])

        for model in ide_models:
            test_name = f"{ide}_{model}"
            print(f"\nTesting {test_name}...")

            cmd = [
                "python", "-m", "pytest",
                "tests/test_ai_model_quality.py",
                f"--ide={ide}",
                f"--model={model}",
                "--verbose",
                "-m", "ai_model"
            ]

            success = run_command(" ".join(cmd))
            results[test_name] = {"success": success, "timestamp": time.time()}

    # Save results
    with open("results/ai_model_quality.json", "w") as f:
        json.dump(results, f, indent=2)

    return True


def generate_comparison_report(ides: List[str]):
    """Generate comprehensive comparison report"""
    print(f"\n=== Generating comparison report ===")

    # This would generate a comprehensive HTML report comparing all results
    # For now, just create a summary

    report_data = {
        "timestamp": time.time(),
        "ides_tested": ides,
        "summary": "Multi-IDE AI Model Benchmark Results"
    }

    with open("reports/comparison_summary.json", "w") as f:
        json.dump(report_data, f, indent=2)

    print("Comparison report generated: reports/comparison_summary.json")
    return True


def main():
    """Main function"""
    parser = argparse.ArgumentParser(
        description="Multi-IDE AI Model Benchmark Test Runner"
    )

    # IDE selection
    parser.add_argument(
        "--ide",
        choices=list(SUPPORTED_IDES.keys()) + ["all"],
        default="cursor",
        help="IDE to test (default: cursor)"
    )

    parser.add_argument(
        "--ides",
        help="Comma-separated list of IDEs to test"
    )

    # Model selection
    parser.add_argument(
        "--model",
        help="Specific AI model to test"
    )

    parser.add_argument(
        "--models",
        help="Comma-separated list of models to test"
    )

    # Test categories
    parser.add_argument(
        "--basic",
        action="store_true",
        help="Run basic functionality tests"
    )

    parser.add_argument(
        "--performance",
        action="store_true",
        help="Run performance benchmarks"
    )

    parser.add_argument(
        "--workflows",
        action="store_true",
        help="Run workflow tests"
    )

    parser.add_argument(
        "--cross-ide",
        action="store_true",
        help="Run cross-IDE comparison tests"
    )

    parser.add_argument(
        "--ai-models",
        action="store_true",
        help="Run AI model quality tests"
    )

    parser.add_argument(
        "--all-tests",
        action="store_true",
        help="Run all test categories"
    )

    # Special modes
    parser.add_argument(
        "--all-ides",
        action="store_true",
        help="Test all available IDEs"
    )

    parser.add_argument(
        "--all-models",
        action="store_true",
        help="Test all available models for each IDE"
    )

    parser.add_argument(
        "--quick",
        action="store_true",
        help="Run quick tests only"
    )

    parser.add_argument(
        "--comprehensive",
        action="store_true",
        help="Run comprehensive benchmark suite"
    )

    parser.add_argument(
        "--headless",
        action="store_true",
        help="Run in headless mode"
    )

    parser.add_argument(
        "--generate-report",
        action="store_true",
        help="Generate comparison report"
    )

    args = parser.parse_args()

    # Setup environment
    setup_environment()

    # Check API keys
    print("\n=== Checking API Keys ===")
    api_keys = check_api_keys()

    # Parse IDEs to test
    if args.all_ides:
        ides_to_test = list(SUPPORTED_IDES.keys())
    elif args.ides:
        ides_to_test = [ide.strip() for ide in args.ides.split(",")]
    elif args.ide == "all":
        ides_to_test = list(SUPPORTED_IDES.keys())
    else:
        ides_to_test = [args.ide]

    # Parse models to test
    models_to_test = None
    if args.models:
        models_to_test = [model.strip() for model in args.models.split(",")]
    elif args.model:
        models_to_test = [args.model]

    # Determine test categories
    test_categories = []
    if args.basic or args.quick:
        test_categories.append("basic")
    if args.performance or args.comprehensive:
        test_categories.append("performance")
    if args.workflows or args.comprehensive:
        test_categories.append("workflows")
    if args.all_tests or args.comprehensive:
        test_categories.extend(["basic", "performance", "workflows"])

    if not test_categories:
        test_categories = ["basic"]  # Default

    # Remove duplicates
    test_categories = list(set(test_categories))

    print(f"\n=== Test Configuration ===")
    print(f"IDEs to test: {', '.join(ides_to_test)}")
    print(f"Test categories: {', '.join(test_categories)}")
    if models_to_test:
        print(f"Models to test: {', '.join(models_to_test)}")

    # Run tests
    overall_success = True

    # Run IDE-specific tests
    for ide in ides_to_test:
        success = run_ide_tests(ide, models_to_test, test_categories)
        if not success:
            overall_success = False

    # Run cross-IDE tests if multiple IDEs
    if args.cross_ide or (len(ides_to_test) > 1 and args.comprehensive):
        success = run_cross_ide_comparison(ides_to_test, models_to_test)
        if not success:
            overall_success = False

    # Run performance benchmarks
    if args.performance or args.comprehensive:
        success = run_performance_benchmarks(ides_to_test, models_to_test)
        if not success:
            overall_success = False

    # Run AI model quality tests
    if args.ai_models or args.comprehensive:
        success = run_ai_model_quality_tests(ides_to_test, models_to_test)
        if not success:
            overall_success = False

    # Generate comparison report
    if args.generate_report or args.comprehensive:
        generate_comparison_report(ides_to_test)

    # Final status
    print(f"\n=== Test Results ===")
    if overall_success:
        print("✓ All tests completed successfully!")
        sys.exit(0)
    else:
        print("✗ Some tests failed - check logs above")
        sys.exit(1)


if __name__ == "__main__":
    main()
