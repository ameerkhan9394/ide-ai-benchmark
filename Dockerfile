# Multi-IDE AI Model Benchmark Framework
# Supports testing across Cursor, Windsurf, VSCode, and other IDEs

FROM python:3.13-slim

# Install system dependencies
RUN apt-get update && apt-get install -y \
    # X11 and GUI support
    xvfb \
    x11-utils \
    xdotool \
    scrot \
    wmctrl \
    # Python GUI dependencies
    python3-tk \
    python3-dev \
    # X11 libraries
    libxtst6 \
    libxss1 \
    libgtk-3-0 \
    libgconf-2-4 \
    libasound2 \
    libatk-bridge2.0-0 \
    libdrm2 \
    libxkbcommon0 \
    libxcomposite1 \
    libxdamage1 \
    libxrandr2 \
    libgbm1 \
    libxss1 \
    libasound2 \
    # Additional dependencies for IDEs
    libgtk-3-0 \
    libgbm-dev \
    libnss3 \
    libatk-bridge2.0-0 \
    libdrm2 \
    libxkbcommon0 \
    libxcomposite1 \
    libxdamage1 \
    libxrandr2 \
    # Build tools
    build-essential \
    wget \
    curl \
    unzip \
    # Process management
    procps \
    psmisc \
    # Networking
    ca-certificates \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Create test user with proper permissions
RUN useradd -m -s /bin/bash testuser && \
    usermod -aG sudo testuser && \
    echo 'testuser ALL=(ALL) NOPASSWD:ALL' >> /etc/sudoers

# Copy requirements and install Python dependencies
COPY pyproject.toml uv.lock* ./
RUN pip install uv && \
    uv sync --extra test

# Set up environment variables
ENV DISPLAY=:99
ENV PYTHONPATH=/app/src
ENV QT_X11_NO_MITSHM=1
ENV XDG_RUNTIME_DIR=/tmp/runtime-testuser
ENV CONTAINER=true

# Create necessary directories
RUN mkdir -p /app/screenshots /app/test_images /app/reports /app/results /app/logs && \
    mkdir -p /tmp/runtime-testuser && \
    chown -R testuser:testuser /app /tmp/runtime-testuser

# Copy source code
COPY --chown=testuser:testuser . .

# Switch to test user
USER testuser

# Create Xvfb startup script
RUN echo '#!/bin/bash\n\
# Start Xvfb\n\
Xvfb :99 -screen 0 1920x1080x24 -ac +extension GLX &\n\
XVFB_PID=$!\n\
echo "Started Xvfb with PID: $XVFB_PID"\n\
\n\
# Wait for display to be ready\n\
sleep 3\n\
\n\
# Export display\n\
export DISPLAY=:99\n\
\n\
# Function to cleanup on exit\n\
cleanup() {\n\
    echo "Cleaning up..."\n\
    # Kill any running IDE processes\n\
    pkill -f "cursor\\|windsurf\\|code" || true\n\
    # Kill Xvfb\n\
    kill $XVFB_PID 2>/dev/null || true\n\
    exit 0\n\
}\n\
\n\
# Set up signal handlers\n\
trap cleanup SIGTERM SIGINT\n\
\n\
# Execute the main command\n\
exec "$@"\n\
' > /app/docker-entrypoint.sh && \
    chmod +x /app/docker-entrypoint.sh

# Health check script
RUN echo '#!/bin/bash\n\
# Check if Xvfb is running\n\
pgrep Xvfb > /dev/null || exit 1\n\
\n\
# Check if display is working\n\
DISPLAY=:99 xdpyinfo > /dev/null 2>&1 || exit 1\n\
\n\
# Check if Python environment is working\n\
python -c "import sys; sys.path.insert(0, \"/app/src\"); from ide_automation import create_ide_automation" || exit 1\n\
\n\
echo "Health check passed"\n\
exit 0\n\
' > /app/healthcheck.sh && \
    chmod +x /app/healthcheck.sh

# Expose any necessary ports (none needed for this application)
# EXPOSE 8080

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD /app/healthcheck.sh

# Volume for IDE applications (mount your IDEs here)
VOLUME ["/app/ides"]

# Volume for test results
VOLUME ["/app/results", "/app/reports", "/app/screenshots"]

# Default command - run quick benchmark
ENTRYPOINT ["/app/docker-entrypoint.sh"]
CMD ["python", "scripts/run_tests.py", "--quick", "--headless"]

# Usage Examples:
#
# Build:
# docker build -t ide-ai-benchmark .
#
# Run with Cursor IDE:
# docker run -v /path/to/cursor.AppImage:/app/ides/cursor.AppImage \
#            -v /path/to/results:/app/results \
#            -e CURSOR_PATH=/app/ides/cursor.AppImage \
#            -e ANTHROPIC_API_KEY=your_key \
#            ide-ai-benchmark
#
# Run cross-IDE comparison:
# docker run -v /path/to/ides:/app/ides \
#            -v /path/to/results:/app/results \
#            -e CURSOR_PATH=/app/ides/cursor.AppImage \
#            -e WINDSURF_PATH=/app/ides/windsurf.AppImage \
#            -e VSCODE_PATH=/usr/bin/code \
#            -e ANTHROPIC_API_KEY=your_key \
#            -e OPENAI_API_KEY=your_key \
#            ide-ai-benchmark python scripts/run_tests.py --cross-ide --all-ides
#
# Interactive mode:
# docker run -it -v /path/to/ides:/app/ides ide-ai-benchmark bash
#
# Custom benchmark:
# docker run -v /path/to/ides:/app/ides \
#            -v /path/to/results:/app/results \
#            ide-ai-benchmark python scripts/run_tests.py --ide cursor --performance
