#!/bin/bash

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

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

CURSOR_APPIMAGE="./cursor.AppImage"
DOWNLOAD_URL="https://www.cursor.com/download/stable/linux-x64"

# Check if cursor.AppImage already exists
if [[ -f "$CURSOR_APPIMAGE" ]]; then
  FILE_SIZE=$(stat -f%z "$CURSOR_APPIMAGE" 2>/dev/null || stat -c%s "$CURSOR_APPIMAGE" 2>/dev/null)
  print_success "Cursor AppImage already exists: $CURSOR_APPIMAGE ($(($FILE_SIZE / 1024 / 1024))MB)"
  print_status "Use --force to re-download"
  if [[ "$1" != "--force" ]]; then
    exit 0
  fi
fi

print_status "Downloading Cursor AppImage..."
print_status "URL: $DOWNLOAD_URL"
print_status "Target: $CURSOR_APPIMAGE"

# Download with progress
if command -v wget >/dev/null 2>&1; then
  if wget --progress=bar:force:noscroll -O "$CURSOR_APPIMAGE" "$DOWNLOAD_URL"; then
    print_success "Download completed!"
  else
    print_error "Download failed with wget"
    rm -f "$CURSOR_APPIMAGE"
    exit 1
  fi
elif command -v curl >/dev/null 2>&1; then
  if curl -L --progress-bar -o "$CURSOR_APPIMAGE" "$DOWNLOAD_URL"; then
    print_success "Download completed!"
  else
    print_error "Download failed with curl"
    rm -f "$CURSOR_APPIMAGE"
    exit 1
  fi
else
  print_error "Neither wget nor curl found. Please install one of them."
  exit 1
fi

# Make executable
chmod +x "$CURSOR_APPIMAGE"

# Verify the file
if [[ -f "$CURSOR_APPIMAGE" ]]; then
  FILE_SIZE=$(stat -f%z "$CURSOR_APPIMAGE" 2>/dev/null || stat -c%s "$CURSOR_APPIMAGE" 2>/dev/null)
  if [[ $FILE_SIZE -gt 50000000 ]]; then # At least 50MB
    print_success "Cursor AppImage downloaded successfully! ($(($FILE_SIZE / 1024 / 1024))MB)"
    print_status "You can now run: ./scripts/run-tests-docker.sh"
  else
    print_error "Downloaded file seems too small ($(($FILE_SIZE / 1024 / 1024))MB). Download may have failed."
    exit 1
  fi
else
  print_error "Download verification failed"
  exit 1
fi
