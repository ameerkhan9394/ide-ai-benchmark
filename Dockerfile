FROM ubuntu:24.04

# Avoid prompts from apt
ENV DEBIAN_FRONTEND=noninteractive

# Add deadsnakes PPA for Python 3.13
RUN apt-get update && apt-get install -y software-properties-common && \
  add-apt-repository ppa:deadsnakes/ppa && \
  apt-get update

# Install system dependencies including OpenCV requirements
RUN apt-get install -y \
  python3.13 \
  python3.13-dev \
  python3.13-venv \
  python3.13-tk \
  python3-pip \
  curl \
  wget \
  xvfb \
  x11vnc \
  x11-utils \
  fluxbox \
  wmctrl \
  xdotool \
  imagemagick \
  fonts-liberation \
  libnss3-dev \
  libatk-bridge2.0-0 \
  libdrm2 \
  libxkbcommon0 \
  libgtk-3-0 \
  libxss1 \
  libasound2t64 \
  libxtst6 \
  libxrandr2 \
  python3-dev \
  python3-setuptools \
  libx11-dev \
  libxinerama1 \
  libxcursor1 \
  libxi6 \
  libglib2.0-0 \
  libsm6 \
  libxext6 \
  libxrender-dev \
  libgoogle-glog-dev \
  libgflags-dev \
  libatlas-base-dev \
  libhdf5-103-1t64 \
  libhdf5-dev \
  libavcodec-dev \
  libavformat-dev \
  libswscale-dev \
  libgstreamer1.0-dev \
  libgstreamer-plugins-base1.0-dev \
  libjpeg-dev \
  libpng-dev \
  libtiff-dev \
  libwebp-dev \
  libopenexr-dev \
  libopenblas-dev && \
  rm -rf /var/lib/apt/lists/*

# Create a non-root user
RUN useradd -m -s /bin/bash testuser
USER testuser
WORKDIR /home/testuser

# Set up virtual environment
RUN python3.13 -m venv venv
ENV PATH="/home/testuser/venv/bin:$PATH"

# Install uv for faster package management
RUN pip install uv

# Copy project files
COPY --chown=testuser:testuser . /home/testuser/cursor-benchmark/
WORKDIR /home/testuser/cursor-benchmark

# Create Applications directory first
RUN mkdir -p /home/testuser/Applications

# Copy local cursor.AppImage if it exists, otherwise download it
RUN if [ -f "./cursor.AppImage" ]; then \
        echo "Using local cursor.AppImage from project root"; \
        cp ./cursor.AppImage /home/testuser/Applications/cursor.AppImage; \
        chmod +x /home/testuser/Applications/cursor.AppImage; \
    else \
        echo "No local cursor.AppImage found, downloading..."; \
        wget -O /home/testuser/Applications/cursor.AppImage \
            "https://www.cursor.com/download/stable/linux-x64" && \
        chmod +x /home/testuser/Applications/cursor.AppImage; \
    fi

# Extract AppImage since FUSE is not available in containers
RUN cd /home/testuser/Applications && \
    ./cursor.AppImage --appimage-extract && \
    mv squashfs-root cursor-extracted && \
    ln -sf /home/testuser/Applications/cursor-extracted/cursor /home/testuser/Applications/cursor && \
    echo "AppImage extracted successfully"

# Install Python dependencies
RUN uv sync --extra test

# Update PATH to use the project's .venv created by uv
ENV PATH="/home/testuser/cursor-benchmark/.venv/bin:$PATH"

# Create Applications directory
RUN mkdir -p /home/testuser/Applications

# Note: Cursor AppImage will be mounted at runtime via docker-compose volumes

# Set up display environment
ENV DISPLAY=:99
ENV XAUTHORITY=/home/testuser/.Xauthority

# Create X11 socket directory and set permissions
USER root
RUN mkdir -p /tmp/.X11-unix && chmod 1777 /tmp/.X11-unix
USER testuser

# Create startup script with better X11 handling
RUN echo '#!/bin/bash\n\
set -e\n\
\n\
# Function to cleanup processes\n\
cleanup() {\n\
    echo "Cleaning up processes..."\n\
    if [ ! -z "$WM_PID" ]; then\n\
        echo "Terminating window manager..."\n\
        kill -TERM $WM_PID 2>/dev/null || true\n\
        sleep 2\n\
        kill -KILL $WM_PID 2>/dev/null || true\n\
    fi\n\
    if [ ! -z "$XVFB_PID" ]; then\n\
        echo "Terminating Xvfb..."\n\
        kill -TERM $XVFB_PID 2>/dev/null || true\n\
        sleep 2\n\
        kill -KILL $XVFB_PID 2>/dev/null || true\n\
    fi\n\
    echo "Cleanup complete"\n\
}\n\
\n\
# Set up signal handlers\n\
trap cleanup EXIT INT TERM\n\
\n\
# Create X11 auth file\n\
touch $XAUTHORITY\n\
\n\
# Start Xvfb with better error handling\n\
echo "Starting Xvfb..."\n\
Xvfb $DISPLAY -screen 0 1920x1080x24 -ac +extension GLX +render -noreset -dpi 96 &\n\
XVFB_PID=$!\n\
\n\
# Wait for X server to be ready\n\
echo "Waiting for X server to start..."\n\
for i in {1..30}; do\n\
    if xdpyinfo -display $DISPLAY >/dev/null 2>&1; then\n\
        echo "X server is ready"\n\
        break\n\
    fi\n\
    if [ $i -eq 30 ]; then\n\
        echo "X server failed to start within 30 seconds"\n\
        exit 1\n\
    fi\n\
    sleep 1\n\
done\n\
\n\
# Start window manager\n\
echo "Starting window manager..."\n\
fluxbox -display $DISPLAY &\n\
WM_PID=$!\n\
\n\
# Wait for WM to be ready\n\
sleep 3\n\
\n\
# Verify WM is running\n\
if ! wmctrl -m >/dev/null 2>&1; then\n\
    echo "Warning: Window manager may not be running properly"\n\
fi\n\
\n\
echo "Display environment ready"\n\
echo "Running command: $@"\n\
\n\
# Run the command passed as arguments\n\
"$@"\n\
EXIT_CODE=$?\n\
\n\
echo "Command finished with exit code: $EXIT_CODE"\n\
\n\
exit $EXIT_CODE\n\
' >/home/testuser/run-with-display.sh && chmod +x /home/testuser/run-with-display.sh

# Create test runner script that uses the copied Cursor AppImage
RUN echo '#!/bin/bash\n\
echo "=== STARTING CURSOR AUTOMATION TESTS IN CONTAINER ==="\n\
echo "Container Display: $DISPLAY"\n\
\n\
# Verify Cursor AppImage is available\n\
if [ -f "/home/testuser/Applications/cursor.AppImage" ]; then\n\
    echo "Using Cursor AppImage from container"\n\
    ls -la /home/testuser/Applications/cursor.AppImage\n\
else\n\
    echo "ERROR: Cursor AppImage not found in container"\n\
    exit 1\n\
fi\n\
\n\
echo "Cursor AppImage: /home/testuser/Applications/cursor.AppImage"\n\
echo ""\n\
\n\
# Update config to use container paths\n\
export CURSOR_PATH="/home/testuser/Applications/cursor.AppImage"\n\
\n\
# Run tests with virtual display\n\
echo "=== RUNNING TESTS ==="\n\
exec /home/testuser/run-with-display.sh python scripts/run_tests.py "$@"\n\
' >/home/testuser/run-tests.sh && chmod +x /home/testuser/run-tests.sh

# Default command
CMD ["/home/testuser/run-tests.sh", "--quick"]
