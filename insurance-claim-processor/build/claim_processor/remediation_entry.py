"""Remediation Lambda entry — SNS alarm in, bounded AppConfig flag flip out (F10).

The pure mapping lives in `remediation.py`; this module is the thin applier:
parse the CloudWatch alarm notification SNS delivers, decide, and apply the
decision as a read-modify-write of the AppConfig document (data-plane read of
what is live, `CreateHostedConfigurationVersion`, `StartDeployment`). Only
flag flips are applied — `switch_model` and `rollback_deployment` are recorded
but need a human (a candidate model id / an in-flight deployment) and stay
no-ops here. Every decision is logged as the AC-Q5 `remediation_record`.

Lambda handler string: `claim_processor.remediation_entry.lambda_handler`.
Env: CLAIM_PROCESSOR_APPCONFIG_APP_ID / _ENV_ID / _PROFILE_ID (control-plane
IDs, not names), CLAIM_PROCESSOR_EXTRACT_MODEL_ID (the breaker target),
CLAIM_PROCESSOR_REMEDIATION_STRATEGY (default AppConfig.AllAtOnce — a flag
flip must land now, not bake).
"""

from __future__ import annotations

import json
import logging
import os
from typing import Any

from claim_processor.remediation import (
    RemediationAction,
    RemediationDecision,
    decide_remediation,
    remediation_record,
)

logger = logging.getLogger("claim_processor.remediation")
logger.setLevel(logging.INFO)

_ALARM_PREFIX = "claim-processor-"

_appconfig: Any = None
_appconfigdata: Any = None


def apply_to_flags(decision: RemediationDecision, flags: dict[str, Any]) -> dict[str, Any] | None:
    """Return the updated flags for a flag-flip action, or None when there is
    nothing to change (wrong action kind, or the flag already holds)."""
    if decision.action == RemediationAction.OPEN_BREAKER:
        open_models = list(flags.get("breaker_open_models") or [])
        if not decision.target or decision.target in open_models:
            return None
        return {**flags, "breaker_open_models": open_models + [decision.target]}
    if decision.action == RemediationAction.CLOSE_BREAKER:
        open_models = list(flags.get("breaker_open_models") or [])
        if not decision.target or decision.target not in open_models:
            return None
        open_models.remove(decision.target)
        return {**flags, "breaker_open_models": open_models}
    if decision.action == RemediationAction.DISABLE_ENSEMBLE:
        if flags.get("kill_switch_ensemble") is True:
            return None
        return {**flags, "kill_switch_ensemble": True}
    return None


def _clients() -> tuple[Any, Any]:
    global _appconfig, _appconfigdata
    if _appconfig is None or _appconfigdata is None:
        import boto3

        region = os.environ.get("CLAIM_PROCESSOR_REGION", "us-east-1")
        _appconfig = boto3.client("appconfig", region_name=region)
        _appconfigdata = boto3.client("appconfigdata", region_name=region)
    return _appconfig, _appconfigdata


def _read_live_document(appconfigdata: Any, app: str, env: str, profile: str) -> dict[str, Any]:
    session = appconfigdata.start_configuration_session(
        ApplicationIdentifier=app,
        EnvironmentIdentifier=env,
        ConfigurationProfileIdentifier=profile,
    )
    resp = appconfigdata.get_latest_configuration(
        ConfigurationToken=session["InitialConfigurationToken"]
    )
    return json.loads(resp["Configuration"].read().decode("utf-8"))


def _deploy_document(
    appconfig: Any, document: dict[str, Any], app: str, env: str, profile: str, strategy: str
) -> dict[str, Any]:
    version = appconfig.create_hosted_configuration_version(
        ApplicationId=app,
        ConfigurationProfileId=profile,
        ContentType="application/json",
        Content=json.dumps(document, indent=2).encode("utf-8"),
    )
    deployment = appconfig.start_deployment(
        ApplicationId=app,
        EnvironmentId=env,
        DeploymentStrategyId=strategy,
        ConfigurationProfileId=profile,
        ConfigurationVersion=str(version["VersionNumber"]),
        Description=f"remediation flag flip (version {version['VersionNumber']})",
    )
    return {
        "config_version": version["VersionNumber"],
        "deployment_number": deployment["DeploymentNumber"],
    }


def _alarm_messages(event: dict[str, Any]) -> list[dict[str, Any]]:
    """CloudWatch alarm payloads from an SNS event (or one direct test payload)."""
    records = event.get("Records")
    if not isinstance(records, list):
        return [event] if "AlarmName" in event else []
    out = []
    for record in records:
        raw = ((record or {}).get("Sns") or {}).get("Message")
        if raw:
            try:
                out.append(json.loads(raw))
            except (TypeError, ValueError):
                logger.warning("remediation: non-JSON SNS message ignored")
    return out


def lambda_handler(
    event: dict[str, Any],
    context: Any = None,
    *,
    appconfig: Any = None,
    appconfigdata: Any = None,
    environ: dict[str, str] | None = None,
) -> dict[str, Any]:
    env_vars = environ if environ is not None else dict(os.environ)
    app = env_vars["CLAIM_PROCESSOR_APPCONFIG_APP_ID"]
    env_id = env_vars["CLAIM_PROCESSOR_APPCONFIG_ENV_ID"]
    profile = env_vars["CLAIM_PROCESSOR_APPCONFIG_PROFILE_ID"]
    strategy = env_vars.get("CLAIM_PROCESSOR_REMEDIATION_STRATEGY", "AppConfig.AllAtOnce")
    target = env_vars.get("CLAIM_PROCESSOR_EXTRACT_MODEL_ID")

    results: list[dict[str, Any]] = []
    for message in _alarm_messages(event):
        alarm_full = str(message.get("AlarmName", ""))
        alarm = alarm_full.removeprefix(_ALARM_PREFIX)
        state = str(message.get("NewStateValue", ""))
        decision = decide_remediation(alarm, state, target=target)
        record: dict[str, Any] = remediation_record(decision)

        if decision.action in (
            RemediationAction.OPEN_BREAKER,
            RemediationAction.CLOSE_BREAKER,
            RemediationAction.DISABLE_ENSEMBLE,
        ):
            if appconfig is None or appconfigdata is None:
                appconfig, appconfigdata = _clients()
            document = _read_live_document(appconfigdata, app, env_id, profile)
            new_flags = apply_to_flags(decision, document.get("flags") or {})
            if new_flags is None:
                record["applied"] = False
                record["reason"] = "already in desired state"
            else:
                document["flags"] = new_flags
                # A ConflictException (deployment in flight) propagates: the
                # Lambda errors, SNS redelivers, the retry applies the flip.
                record.update(_deploy_document(appconfig, document, app, env_id, profile, strategy))
                record["applied"] = True
        elif decision.action != RemediationAction.NONE:
            record["applied"] = False
            record["reason"] = "needs a human (no candidate model / no in-flight deployment)"
        else:
            record["applied"] = False

        logger.info(json.dumps({"remediation_record": record}))
        results.append(record)

    return {"records": results}
