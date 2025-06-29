#!/bin/bash

# install-deps.sh – System dependencies for SnapGuard
# Supported Linux distros: Debian, Ubuntu

set -e

echo "SnapGuard – Installing system dependencies"
echo

# Check if the script is running with root privileges
if [[ $EUID -ne 0 ]]; then
  if ! command -v sudo >/dev/null 2>&1; then
    echo "Please run this script as root or with sudo."
    exit 1
  fi
  SUDO="sudo"
else
  SUDO=""
fi

# Define package list
PACKAGES=(
  libgirepository1.0-dev
  gir1.2-gtk-3.0
  libcairo2-dev
  libdbus-1-dev
  libsystemd-dev
  python3-dev
  pkg-config
  cmake
  build-essential
  python3-venv
)

echo "Updating package list..."
$SUDO apt update

echo "Installing required packages:"
echo "  ${PACKAGES[*]}"
$SUDO apt install -y "${PACKAGES[@]}"

echo
echo "✔ All system dependencies for SnapGuard have been installed."
echo "Creating a virtual environment and installing dependencies from requirements.txt:"
echo
echo "  python3 -m venv .venv"
echo "  source .venv/bin/activate"
echo "  pip install --upgrade pip"
echo "  pip install -r requirements.txt"
echo
echo "Done."
