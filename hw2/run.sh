#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")"
nohup python3 you_agent_nanda.py > out.log 2>&1 &
echo "Started. Tail logs with: tail -n 100 out.log"
