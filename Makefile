.PHONY: help install test test-basic test-performance test-workflow test-all test-quick test-coverage clean setup ci-setup format lint

help:
	@echo "ImBIOS's Cursor Model Benchmark"
	@echo "================================"
	@echo ""
	@echo "Available targets:"
	@echo "  help            - Show this help message"
	@echo "  install         - Install Python dependencies"
	@echo "  setup           - Setup development environment"
	@echo "  test            - Run quick tests"
	@echo "  test-basic      - Run basic functionality tests"
	@echo "  test-performance - Run performance benchmark tests"
	@echo "  test-workflow   - Run user workflow tests"
	@echo "  test-all        - Run all tests"
	@echo "  test-quick      - Run quick tests (excluding slow ones)"
	@echo "  test-coverage   - Run tests with coverage"
	@echo "  test-headless   - Run tests in headless mode"
	@echo "  ci-setup        - Setup CI environment"
	@echo "  format          - Format code with black"
	@echo "  lint            - Run linters"
	@echo "  clean           - Clean up generated files"
	@echo ""

install:
	pip install -r requirements.txt

setup:
	pip install -r requirements.txt
	pip install pytest-cov black flake8
	mkdir -p reports screenshots test_images
	chmod +x scripts/run_tests.py

test:
	python scripts/run_tests.py --quick

test-basic:
	python scripts/run_tests.py --basic

test-performance:
	python scripts/run_tests.py --performance

test-workflow:
	python scripts/run_tests.py --workflow

test-all:
	python scripts/run_tests.py --all

test-quick:
	python scripts/run_tests.py --quick

test-coverage:
	python scripts/run_tests.py --coverage

test-headless:
	@echo "Starting Xvfb for headless testing..."
	Xvfb :99 -screen 0 1920x1080x24 &
	@sleep 2
	DISPLAY=:99 python scripts/run_tests.py --headless --all
	@pkill Xvfb

ci-setup:
	sudo apt-get update
	sudo apt-get install -y xvfb x11-utils xdotool scrot python3-tk python3-dev libxtst6 libxss1 libgconf-2-4 libasound2 libgtk-3-0
	pip install -r requirements.txt
	mkdir -p reports screenshots test_images

format:
	black src/ tests/ scripts/

lint:
	flake8 src/ tests/ scripts/
	black --check src/ tests/ scripts/

clean:
	rm -rf __pycache__ .pytest_cache htmlcov .coverage coverage.xml
	rm -rf reports screenshots test_images
	find . -name "*.pyc" -delete
	find . -name "*.pyo" -delete
	find . -name "*~" -delete
	rm -f *.json *.html *.xml

# Development targets
dev-install:
	pip install -e .
	pip install pytest-cov black flake8 mypy

type-check:
	mypy src/

# Docker targets (for containerized testing)
docker-build:
	docker build -t cursor-testing .

docker-test:
	docker run --rm -v $(PWD):/app cursor-testing make test-headless

# Quick development workflow
dev: format lint test-quick

# CI simulation
ci: format lint test-coverage

# Template creation
templates:
	python scripts/run_tests.py --templates

# Benchmark only
benchmark:
	python -m pytest tests/test_performance_benchmarks.py -v --html=reports/benchmark-report.html

# Watch mode for development
watch:
	@echo "Watching for changes... Press Ctrl+C to stop"
	while true; do \
		inotifywait -e modify -r src/ tests/ || break; \
		make test-quick; \
		sleep 1; \
	done