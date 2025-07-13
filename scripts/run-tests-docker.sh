#!/bin/bash

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
  echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
  echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
  echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
  echo -e "${RED}[ERROR]${NC} $1"
}

# Check if Docker is running
if ! docker info >/dev/null 2>&1; then
  print_error "Docker is not running. Please start Docker and try again."
  exit 1
fi

# Check if docker-compose is available
if ! command -v docker-compose &>/dev/null; then
  print_error "docker-compose is not installed. Please install it and try again."
  exit 1
fi

print_status "Starting Cursor automation tests in Docker container..."
print_status "This will run in complete isolation from your host Cursor session."

# Create directories for output
mkdir -p reports screenshots logs

# Build the container if it doesn't exist or if --rebuild is passed
if [[ "$1" == "--rebuild" ]] || ! docker image inspect cursor-benchmark_cursor-benchmark >/dev/null 2>&1; then
  print_status "Building Docker container..."
  if docker-compose build; then
    print_success "Container built successfully"
  else
    print_error "Failed to build container"
    exit 1
  fi
  # Remove --rebuild from arguments if it was there
  if [[ "$1" == "--rebuild" ]]; then
    shift
  fi
fi

# Default to quick tests if no arguments provided
if [[ $# -eq 0 ]]; then
  set -- "--quick"
fi

print_status "Running tests with arguments: $*"
print_status "Results will be saved to:"
print_status "  - Reports: ./reports/"
print_status "  - Screenshots: ./screenshots/"
print_status "  - Logs: ./logs/"

# Note: Cursor AppImage is now built into the container from the project root
if [[ -f "./cursor.AppImage" ]]; then
  print_status "Found local cursor.AppImage - will be used in container"
else
  print_status "No local cursor.AppImage found - will be downloaded in container"
fi

# Run the container with the provided arguments
if docker-compose run --rm cursor-benchmark /home/testuser/run-tests.sh "$@"; then
  print_success "Tests completed successfully!"
  print_status "Check the reports/ directory for detailed results."
  EXIT_CODE=0
else
  print_error "Tests failed. Check the logs/ directory for details."
  EXIT_CODE=1
fi

exit $EXIT_CODE
