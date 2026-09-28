"""Stage 18 — host the whole triage squad on Bedrock AgentCore Runtime.

The AgentCore SDK turns this file into the HTTP server the runtime calls
(POST /invocations, GET /ping). We decorate one entrypoint; app.run() serves it.
The squad code is unchanged: make_session() falls back to the runtime's execution
role inside the container, so the same squad.py runs local and hosted.

Payload contract: {"prompt": "<customer message>", "session_id": "<optional>"}
Returns: {"routed_to": "<specialist>", "answer": "<text>"}
"""

from bedrock_agentcore import BedrockAgentCoreApp

from squad import route

app = BedrockAgentCoreApp()


@app.entrypoint
async def invoke(payload):
    message = payload.get("prompt") or payload.get("message") or ""
    session_id = payload.get("session_id", "agentcore")
    return await route(message, user_id="agentcore", session_id=session_id)


if __name__ == "__main__":
    app.run()
