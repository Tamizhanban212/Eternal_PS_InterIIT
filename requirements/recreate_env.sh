#!/usr/bin/env bash
set -euo pipefail

# Script to (re)create the `eternal` conda environment from `environment.yml`
# Usage: cd requirements && ./recreate_env.sh

ENV_FILE="environment.yml"
ENV_NAME="eternal"

if ! command -v conda &> /dev/null; then
  echo "Error: conda not found in PATH. Please install Anaconda/Miniconda or activate conda.")
  exit 1
fi

if [ ! -f "$ENV_FILE" ]; then
  echo "Error: $ENV_FILE not found in $(pwd)"
  exit 1
fi

echo "Removing existing conda env: $ENV_NAME (if present)"
conda env remove -n "$ENV_NAME" -y || true

echo "Creating conda env from $ENV_FILE"
conda env create -f "$ENV_FILE"

echo "Environment '$ENV_NAME' created. To use it run:"
echo "  conda activate $ENV_NAME"

echo "System notes:"
echo "  - On Debian/Ubuntu you may need to install system libs:"
echo "      sudo apt update && sudo apt install -y libzbar0 pigpio"
echo "  - Start pigpio daemon for GPIO access (Raspberry Pi):"
echo "      sudo systemctl enable --now pigpiod"

exit 0
