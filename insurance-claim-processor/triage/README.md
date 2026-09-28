# Claim triage agents

Code-first agent layer for the insurance claim pipeline, built to contrast with
the managed **Bedrock Agents** lab. Two stages:

- **Stage 15 — Strands:** one specialist agent (`status_agent`) built with the
  [Strands Agents](https://strandsagents.com) SDK. The agentic loop runs
  in-process: the model decides which tool to call, our Python code executes it.
- **Stage 16 — Agent Squad:** a classifier routes an incoming customer message to
  the right Strands specialist (status / new-claim / escalation).

No frontend, no API Gateway — driven from a script/test harness. Runs locally
against real Bedrock using the `claim-processor` profile; packaged to Lambda only
after both frameworks work.

## Layout

| File | What |
|---|---|
| `requirements.txt` | `strands-agents` + `boto3` |
| `status_agent.py` | Stage 15: the claim-status specialist (Strands) |

## Run

```bash
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
```
