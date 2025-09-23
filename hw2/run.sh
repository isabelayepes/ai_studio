cat > ~/ai_studio/hw2/run.sh << 'EOF'
#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")"
# registry override to avoid dead :6900; safe to remove later
echo 'https://chat.nanda-registry.com' > registry_url.txt
nohup python3 you_agent_nanda.py > out.log 2>&1 &
echo "Started. Tail logs with: tail -n 100 out.log"
EOF
chmod +x ~/ai_studio/hw2/run.sh
