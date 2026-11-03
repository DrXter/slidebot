#!/usr/bin/env bash
# One-time setup for RHEL 9 / Rocky / Alma (run as a user with sudo).
set -euo pipefail

PY=${PY:-python3.11}

echo "==> System packages"
sudo dnf install -y "${PY}" "${PY}-pip" git curl
# Optional, for slide previews inside the app (LibreOffice renders, poppler makes thumbnails):
sudo dnf install -y libreoffice-impress poppler-utils || echo "LibreOffice/poppler not installed: previews will be disabled"

echo "==> Ollama"
if ! command -v ollama >/dev/null 2>&1; then
  curl -fsSL https://ollama.com/install.sh | sh
fi
sudo systemctl enable --now ollama || true
ollama pull "${MODEL:-qwen2.5:14b}"

echo "==> Python environment"
"${PY}" -m venv .venv
. .venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt

echo
echo "Done. Start the app with:  ./run.sh"
