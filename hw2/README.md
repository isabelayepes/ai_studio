# HW2 — NANDA-wrapped Agent

Disclaimer: ChatGPT was used to help generate this code.

- **Agent:** CrewAI persona agent (from HW1) wrapped with **NANDA Adapter**  
- **Domain:** `myisabelaagent.duckdns.org` (EC2, Let’s Encrypt TLS)  
- **APIs:**  
  - `GET  https://<domain>:6001/api/health` → 200  
  - `POST https://<domain>:6001/api/send`   → `{ agent_id, response }`

## Run (on EC2)
```bash
source ~/venvs/nanda311/bin/activate
pip install -r requirements.txt

# certs in working dir
cp -L /etc/letsencrypt/live/myisabelaagent.duckdns.org/fullchain.pem .
cp -L /etc/letsencrypt/live/myisabelaagent.duckdns.org/privkey.pem   .
chmod 644 fullchain.pem && chmod 600 privkey.pem

export ANTHROPIC_API_KEY="…"
export DOMAIN_NAME="myisabelaagent.duckdns.org"

./run.sh
tail -n 120 out.log

## Checks for Active Ports (EC2)
- `sudo lsof -iTCP -sTCP:LISTEN -P | egrep ':6000|:6001'`
```
## Run (Ollama model on laptop)
- `ollama serve`
- `ollama pull deepseek-r1`
- `python you_agent_ollama.py`
