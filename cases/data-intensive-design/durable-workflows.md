---
type: analysis
title: 'Durable execution and workflows'
description: 'A workflow is a graph of tasks. Durable engines log RPCs and replay past them on failure. Exactly-once still needs idempotent callees and deterministic workflow code.'
tags: [data-intensive-design, encoding, workflows, durable-execution, temporal]
---

# Durable execution and workflows

**See also:** [chapter overview](encoding-overview.md) · [REST and RPC](rest-rpc-dataflow.md) · [event-driven dataflow](event-driven-dataflow.md) · [write-ahead log](b-trees.md#making-b-trees-reliable) · [exactly-once](distributed-transactions.md#exactly-once-message-processing) · [references](encoding-references.md)

A payment that charges a card and deposits to a bank is several
services: fraud, card gateway, bank. One payment is a **workflow** —
a graph of **tasks**. Definitions may be a general-purpose language,
a DSL, or markup such as BPEL ([45](encoding-references.md)). Engines
name tasks differently (Temporal: *activity*; others: *durable
function*); the concept is the same.

A **workflow engine** decides when and where each task runs, what
happens if the machine dies mid-task, and how much may run in
parallel. Typical split: an **orchestrator** schedules, an
**executor** runs. Triggers are a cron, a web service, or a human.

Families of engine:

- Data / ETL: Airflow, Dagster, Prefect.
- Graphical / BPMN for non-engineers: Camunda, Orkes.
- **Durable execution:** Temporal, Restate.

## Exactly-once without a shared transaction

You want each payment once. A crash after the card charge and before
the bank deposit cannot be wrapped in one database transaction — the
gateways are other people’s systems.

Durable execution pretends to give **exactly-once** workflow
semantics. On retry the engine re-runs the task but skips RPCs and
state changes that already succeeded; it returns the logged result
instead. That works because every RPC and state change is appended to
durable storage, like a
[write-ahead log](b-trees.md#making-b-trees-reliable)
([46](encoding-references.md), [47](encoding-references.md)).

A Temporal-shaped fragment:

```python
@workflow.defn
class PaymentWorkflow:
    @workflow.run
    async def run(self, payment: PaymentRequest) -> PaymentResult:
        is_fraud = await workflow.execute_activity(
            check_fraud,
            payment,
            start_to_close_timeout=timedelta(seconds=15),
        )
        if is_fraud:
            return PaymentResultFraudulent
        credit_card_response = await workflow.execute_activity(
            debit_credit_card,
            payment,
            start_to_close_timeout=timedelta(seconds=15),
        )
        # ...
```

Limits:

- External services must still expose an **idempotent** API. Callers
  must send unique IDs ([48](encoding-references.md)).
- Replay expects the **same RPCs in the same order**. Reordering
  function calls can produce undefined behavior
  ([49](encoding-references.md)). Safer: deploy a new workflow
  *version* so in-flight invocations keep the old code
  ([50](encoding-references.md)).
- Replay is **deterministic**. `random` and the system clock are
  hazards; frameworks ship deterministic substitutes, and you have to
  remember to use them. Static checks (Temporal Workflow Check) catch
  some mistakes.

Deterministic replay is powerful and easy to get wrong. A later
chapter on distributed time and order will return to it.

**Architect takeaway:** durable execution is a WAL for control flow,
not a substitute for idempotent callees. Version the workflow
definition the way you version an encoding: in-flight runs stay on
the writer’s version.
