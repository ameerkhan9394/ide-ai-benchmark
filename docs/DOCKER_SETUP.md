# ImBIOS's Cursor Model Benchmark - Docker Setup

This setup allows you to run ImBIOS's Cursor Model Benchmark in a completely isolated Docker container, preventing any interference with your host Cursor session.

## Prerequisites

- Docker installed and running
- docker-compose installed

## Quick Start

### Run Tests (Easy Way)

```bash
# Run quick tests (excludes slow benchmarks)
./scripts/run-tests-docker.sh

# Run all tests
./scripts/run-tests-docker.sh --all

# Run only basic functionality tests
./scripts/run-tests-docker.sh --basic

# Run performance benchmarks
./scripts/run-tests-docker.sh --performance

# Run with coverage
./scripts/run-tests-docker.sh --coverage

# Rebuild container and run tests
./scripts/run-tests-docker.sh --rebuild --quick
```

### Run Tests (Manual Docker Commands)

```bash
# Build the container
docker-compose build

# Run quick tests
docker-compose run --rm cursor-benchmark

# Run with custom arguments
docker-compose run --rm cursor-benchmark /home/testuser/run-tests.sh --all

# Run interactively for debugging
docker-compose run --rm -it cursor-benchmark bash
```

## How It Works

1. **Isolation**: The container runs with its own virtual X11 display (Xvfb)
2. **Clean Environment**: Fresh Cursor AppImage downloaded in container
3. **No Interference**: Your host Cursor session remains untouched
4. **Results Available**: Test results are mounted back to host directories

## Container Environment

- **OS**: Ubuntu 24.04
- **Python**: 3.13 with tkinter support
- **Display**: Virtual X11 display (:99)
- **Window Manager**: Fluxbox (lightweight)
- **Cursor**: Latest AppImage downloaded automatically

## Output Directories

Results are automatically saved to your host machine:

- `./reports/` - HTML test reports
- `./screenshots/` - Screenshots taken during tests
- `./logs/` - Application and test logs

## Troubleshooting

### Container Build Issues

```bash
# Clean rebuild
docker-compose down
docker system prune -f
./scripts/run-tests-docker.sh --rebuild
```

### Permission Issues

```bash
# Fix permissions on output directories
sudo chown -R $USER:$USER reports/ screenshots/ logs/
```

### Debug Mode

```bash
# Run interactively to debug issues
docker-compose run --rm -it cursor-benchmark bash

# Inside container, run tests manually
/home/testuser/run-with-display.sh python scripts/run_tests.py --quick
```

### View Container Logs

```bash
# View build logs
docker-compose build --no-cache

# View runtime logs
docker-compose logs cursor-benchmark
```

## Advanced Usage

### Custom Cursor AppImage

If you want to test with a specific Cursor version:

```bash
# Place your cursor.AppImage in the project root
cp /path/to/your/cursor.AppImage ./cursor.AppImage

# Update Dockerfile to copy local file instead of downloading
# Then rebuild
./scripts/run-tests-docker.sh --rebuild
```

### VNC Access (Optional)

To see what's happening inside the container:

1. Uncomment the x11vnc lines in Dockerfile
2. Rebuild: `./scripts/run-tests-docker.sh --rebuild`
3. Connect with VNC viewer to `localhost:5900`

## Benefits

✅ **Complete Isolation** - No interference with host system
✅ **Reproducible Environment** - Same container every time
✅ **Easy Cleanup** - Remove container when done
✅ **Parallel Testing** - Can run while using host Cursor
✅ **CI/CD Ready** - Perfect for automated testing pipelines

## Performance Notes

- First run takes longer (downloads AppImage ~200MB)
- Subsequent runs are much faster
- Container uses ~2GB RAM during tests
- Virtual display adds minimal overhead
