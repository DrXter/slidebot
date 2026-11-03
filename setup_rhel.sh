#!/usr/bin/env bash
# One-time setup for RHEL 8/9 (and Rocky / Alma). Run from the slidebot folder as a normal user with sudo.
set -euo pipefail
cd "$(dirname "$0")"

echo "==> Python 3.11 (RHEL's default python3 is too old on RHEL 8 and limits Streamlit on RHEL 9)"
pick_python() {
  for p in python3.12 python3.11 python3.10 python3; do
    if command -v "$p" >/dev/null 2>&1 && "$p" -c 'import sys; sys.exit(0 if sys.version_info >= (3, 9) else 1)'; then
      echo "$p"; return 0
    fi
  done
  return 1
}
if [ -z "${PY:-}" ]; then
  if ! command -v python3.11 >/dev/null 2>&1; then
    sudo dnf install -y python3.11 python3.11-pip || true
  fi
  PY=$(pick_python) || { echo "ERROR: no Python 3.9+ found. Install one: sudo dnf install python3.11"; exit 1; }
fi
echo "Using $($PY --version) at $(command -v "$PY")"

echo "==> System packages"
sudo dnf install -y git curl
# Optional, for slide previews inside the app:
sudo dnf install -y libreoffice-impress poppler-utils || echo "LibreOffice/poppler not installed: previews will be disabled"

echo "==> Ollama"
if ! command -v ollama >/dev/null 2>&1; then
  curl -fsSL https://ollama.com/install.sh | sh
fi
sudo systemctl enable --now ollama || true
ollama pull "${MODEL:-qwen2.5:14b}"

echo "==> Python environment"
rm -rf .venv
"$PY" -m venv .venv
. .venv/bin/activate
python -m pip install --upgrade pip setuptools wheel
pip install -r requirements.txt

echo
echo "Done. Start the app with:  ./run.sh"
