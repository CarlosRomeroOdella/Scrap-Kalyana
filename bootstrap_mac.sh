#!/usr/bin/env bash
set -euo pipefail

PY_BIN="python3"
PORT="8000"

echo "🔧 Kalyana Scraper Bootstrap (macOS)"
command -v "$PY_BIN" >/dev/null 2>&1 || { echo "❌ Python3 no encontrado. Instala con: brew install python"; exit 1; }

if [[ ! -d ".venv" ]]; then
  echo "🐍 Creando .venv..."
  "$PY_BIN" -m venv .venv
fi
source .venv/bin/activate

python -m pip install -U pip setuptools wheel
pip install -r requirements.txt

python manage.py migrate

if [[ ! -f ".env" ]]; then
  echo "COOKIE_HEADER=" > .env
  echo "📝 Se creó .env (rellena COOKIE_HEADER desde el dashboard)."
fi

echo "🚀 Ejecutando en http://127.0.0.1:${PORT}"
exec python manage.py runserver 0.0.0.0:${PORT}
