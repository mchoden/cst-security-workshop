#!/bin/bash
set -e
cd "$(dirname "$0")/.."
rm -f victim/workshop.db
echo "🔓 Starting Security Workshop servers..."
export VICTIM_URL=${CODESPACE_NAME:+https://${CODESPACE_NAME}-5000.${GITHUB_CODESPACES_PORT_FORWARDING_DOMAIN}}
export VICTIM_URL=${VICTIM_URL:-http://localhost:5000}
python victim/app.py &
python attacker/app.py &
python internal/app.py &
wait
