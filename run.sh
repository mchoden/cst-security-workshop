#!/bin/bash
set -e
cd "$(dirname "$0")"
rm -f victim/workshop.db
pip install flask PyJWT --break-system-packages -q 2>/dev/null || pip install flask PyJWT -q 2>/dev/null
echo ""
echo "🔓 Security Workshop — Starting 3 servers..."
echo "   Victim:   http://localhost:5000"
echo "   Attacker: http://localhost:5001"
echo "   Internal: http://localhost:5002 (simulated internal network)"
echo "   Flags:    http://localhost:5000/flags"
echo ""
python victim/app.py &
python attacker/app.py &
python internal/app.py &
trap "kill 0" INT TERM
wait
