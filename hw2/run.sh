#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")"

# Optional: stop any previous instance on 6000/6001
pkill -f 'you_agent_nanda|python_a2a|run_ui_agent_https' || true
sleep 1

nohup python3 you_agent_nanda.py > out.log 2>&1 &
echo "Started. Tail logs with: tail -n 120 out.log"

