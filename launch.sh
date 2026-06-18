#!/usr/bin/env bash
# ============================================================
#  Fund Tracker — One-Click Launcher (Git Bash / WSL / Linux)
# ============================================================

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ENV_NAME="fund_tracker"

echo ""
echo "========================================"
echo "  Fund Tracker — Real-time NAV Estimator"
echo "========================================"
echo ""

# Check if conda is available
if ! command -v conda &>/dev/null; then
    echo "[ERROR] Conda not found. Please install Anaconda or Miniconda first."
    exit 1
fi

# Source conda for bash shells
# Try common conda installation paths
if [[ -f /d/anaconda3/etc/profile.d/conda.sh ]]; then
    source /d/anaconda3/etc/profile.d/conda.sh
elif [[ -f "$HOME/miniconda3/etc/profile.d/conda.sh" ]]; then
    source "$HOME/miniconda3/etc/profile.d/conda.sh"
elif [[ -f "$HOME/anaconda3/etc/profile.d/conda.sh" ]]; then
    source "$HOME/anaconda3/etc/profile.d/conda.sh"
else
    # Fallback: use conda's activate directly
    eval "$(conda shell.bash hook)"
fi

# Activate the environment
if ! conda activate "$ENV_NAME" 2>/dev/null; then
    echo "[ERROR] Failed to activate conda environment: $ENV_NAME"
    echo "Please create it with: conda create -n $ENV_NAME python=3.12"
    exit 1
fi

echo "[ OK ] Conda environment \"$ENV_NAME\" activated"
echo "[ OK ] Project directory: $SCRIPT_DIR"
echo ""

# Launch the application
cd "$SCRIPT_DIR"
python main.py

echo ""
echo "[DONE] Fund Tracker closed."
