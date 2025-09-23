# HW2 — Wrap agent with the NANDA Adapter

## Overview
This is my HW2 submission for “Connecting Agents”.  
I wrapped my persona-based CrewAI agent with the **NANDA Adapter** so it runs on EC2, is reachable via HTTPS, and can interoperate with other agents.

**Domain:** `myisabelaagent.duckdns.org`  
**Platform:** Amazon Linux 2023 (Python 3.11)

## Files
- `you_agent_ollama.py` — my original persona agent  
- `you_agent_nanda.py` — wrapper that exposes the agent through NANDA  
- `requirements.txt` — key deps (`nanda-adapter`, `crewai`, `langchain-anthropic`)  
- `run.sh` — helper script to start the agent  
- *(not committed)* `fullchain.pem`, `privkey.pem` — TLS certs  

## Setup (on EC2)
```bash
source ~/venvs/nanda311/bin/activate
pip install -r requirements.txt

# Certs in this folder (symlinks or copies)
ln -sf /etc/letsencrypt/live/myisabelaagent.duckdns.org/fullchain.pem fullchain.pem
ln -sf /etc/letsencrypt/live/myisabelaagent.duckdns.org/privkey.pem   privkey.pem

# Env vars (in shell or ~/.bashrc)
export ANTHROPIC_API_KEY="…"
export DOMAIN_NAME="myisabelaagent.duckdns.org"
```

## Run
```bash
./run.sh
tail -n 50 out.log
```

Expected in logs:
- NANDA initialized  
- Agent bridge on `http://<EC2-IP>:6000`  
- HTTPS API on `https://myisabelaagent.duckdns.org:6001`  
- Enrollment link printed  

## Test Endpoints
```bash
# Health
curl -I https://myisabelaagent.duckdns.org:6001/api/health

# Talk to my agent
curl -s -X POST https://myisabelaagent.duckdns.org:6001/api/send \
  -H 'Content-Type: application/json' \
  -d '{"message":"Introduce yourself in 3 sentences."}'
```

## Registry Note
The adapter generates an enrollment link, but the registry API was unavailable (`:6900` timed out; 443 returned 501/404). I added a `registry_url.txt` override so the agent runs cleanly while waiting for registry fixes. Logs and curl probes are included.

## Feedback
NANDA made it easy to wrap my agent once DNS, certs, and firewall rules were set up. The main pain point was the registry endpoint not working as documented.
