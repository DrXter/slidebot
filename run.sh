#!/usr/bin/env bash
# Start SlideBot. Set PORT to change the port; open http://<host>:PORT in a browser.
set -euo pipefail
cd "$(dirname "$0")"
. .venv/bin/activate
exec streamlit run app.py --server.port "${PORT:-8501}" --server.address "${ADDRESS:-0.0.0.0}" --browser.gatherUsageStats false
