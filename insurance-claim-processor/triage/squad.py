"""Stage 16 — Agent Squad routing three Strands specialists.

Agent Squad's job is ROUTING, not answering. A classifier reads each message and
the specialists' DESCRIPTIONS, picks the best-matching specialist, and the
orchestrator hands the message off. Routing quality is description quality.

The seam between the two frameworks is one class: StrandsSpecialist. Agent Squad
expects an agent with an async process_request; a Strands agent has neither. The
adapter's process_request just runs the Strands loop and wraps the reply — so any
Strands agent becomes an Agent Squad specialist.

Contrast with the lab supervisor: same routing job, but there it was a managed
Bedrock agent deciding inside AWS. Here the classifier runs in-process and prints
which specialist it picked.
"""

from __future__ import annotations

import os
import sys
import asyncio

import boto3
from strands import Agent as StrandsAgent
from strands.models import BedrockModel
from agent_squad.orchestrator import AgentSquad
from agent_squad.agents import Agent, AgentOptions
from agent_squad.classifiers import BedrockClassifier, BedrockClassifierOptions
from agent_squad.types import ConversationMessage, ParticipantRole

# Reuse the Stage 15 status logic (the tool + its prompt) — the IP, not a copy.
from status_agent import get_claim_status, make_session, SYSTEM_PROMPT as STATUS_PROMPT

REGION = os.environ.get("AWS_DEFAULT_REGION", "us-east-1")
MODEL_ID = "us.anthropic.claude-haiku-4-5-20251001-v1:0"

_session = make_session()
_bedrock = _session.client("bedrock-runtime")


def _strands(prompt: str, tools=()) -> StrandsAgent:
    """A quiet Strands agent (no streaming) — the squad prints routing + answer."""
    return StrandsAgent(
        model=BedrockModel(model_id=MODEL_ID, boto_session=_session),
        tools=list(tools),
        system_prompt=prompt,
        callback_handler=None,
    )


# --- the seam: any Strands agent -> an Agent Squad specialist ---
class StrandsSpecialist(Agent):
    def __init__(self, options: AgentOptions, strands_agent: StrandsAgent):
        super().__init__(options)
        self._strands = strands_agent

    async def process_request(self, input_text, user_id, session_id,
                              chat_history, additional_params=None):
        result = self._strands(input_text)  # the Strands loop, in-process
        return ConversationMessage(
            role=ParticipantRole.ASSISTANT.value,
            content=[{"text": str(result)}],
        )


NEW_CLAIM_PROMPT = (
    "You help a customer START a new insurance claim. Tell them what to gather to "
    "file (policy number, date of loss, a description of what happened, and the "
    "amount) and how to submit it. You do NOT look up existing claims. Keep it to "
    "a few plain sentences."
)
ESCALATION_PROMPT = (
    "You handle complaints, disputes about a claim decision, and requests to speak "
    "to a human. Acknowledge the concern, say you are escalating to a human "
    "adjuster, and set the expectation that they will follow up. You do NOT decide "
    "claims yourself. Keep it to a few plain sentences."
)

# The descriptions ARE the routing knob — the classifier matches intent to these.
status = StrandsSpecialist(
    AgentOptions(
        name="status",
        description="Reports the status, decision, and details of an EXISTING "
        "claim when the customer gives a claim id or asks where their claim is.",
    ),
    _strands(STATUS_PROMPT, tools=[get_claim_status]),
)
new_claim = StrandsSpecialist(
    AgentOptions(
        name="new-claim",
        description="Helps a customer START or FILE a NEW insurance claim and "
        "explains what information is needed to submit one.",
    ),
    _strands(NEW_CLAIM_PROMPT),
)
escalation = StrandsSpecialist(
    AgentOptions(
        name="escalation",
        description="Handles complaints, disputes about a claim decision, or "
        "requests to speak to a human adjuster.",
    ),
    _strands(ESCALATION_PROMPT),
)

classifier = BedrockClassifier(BedrockClassifierOptions(
    model_id=MODEL_ID, region=REGION, client=_bedrock,
    # F19: Haiku 4.5 rejects temperature + topP together. The classifier drops
    # any None-valued key, so top_p=None removes topP and keeps temperature=0.0.
    inference_config={"top_p": None},
))
orchestrator = AgentSquad(classifier=classifier)
for a in (status, new_claim, escalation):
    orchestrator.add_agent(a)


async def route(message: str, user_id: str = "cust-1", session_id: str = "sess-1") -> dict:
    """Route one message; return {routed_to, answer}. The reusable core — both
    the CLI below and the AgentCore entrypoint call this."""
    resp = await orchestrator.route_request(message, user_id, session_id)
    picked = getattr(resp.metadata, "agent_name",
                     getattr(resp.metadata, "agent_id", "?"))
    out = resp.output
    text = out.content[0]["text"] if hasattr(out, "content") and out.content else str(out)
    return {"routed_to": picked, "answer": text}


async def ask(message: str, user_id: str = "cust-1", session_id: str = "sess-1") -> None:
    result = await route(message, user_id, session_id)
    print(f"\n>>> {message}")
    print(f"[routed to: {result['routed_to']}]")
    print(result["answer"])


if __name__ == "__main__":
    if len(sys.argv) > 1:
        messages = [" ".join(sys.argv[1:])]
    else:
        messages = [
            "where is my claim auto-fl-clean?",
            "I need to file a new claim for a car accident",
            "I think my claim was wrongly rejected, I want to talk to a person",
        ]

    async def main():
        for m in messages:
            await ask(m)
        print()

    asyncio.run(main())
