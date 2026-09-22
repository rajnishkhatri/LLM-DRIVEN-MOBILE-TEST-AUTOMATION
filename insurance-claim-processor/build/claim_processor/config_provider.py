"""Runtime configuration plane over AWS AppConfig (ADR 0010).

`ConfigProvider` reads the AppConfig Data API through an **injected** client
(Stubber offline), caches last-known-good, and falls back to a bootstrap dict
when AppConfig is unreachable, empty, or malformed — a claim never fails
because config fetch failed (AC-K1). Malformed values are dropped and the
previous good value is retained (AC-K4).

No import-time client (DI preserved). `appconfigdata` ships in botocore — no
new pip dependency.
"""

from __future__ import annotations

import json
import logging
from dataclasses import dataclass
from typing import Any

from botocore.exceptions import BotoCoreError, ClientError

_LOG = logging.getLogger("claim_processor.config_provider")

_MODEL_ID_KEYS = ("extract_model_id", "summary_model_id", "understand_model_id")


@dataclass
class ConfigResult:
    config: dict[str, Any]
    source: str  # "appconfig" | "cache" | "fallback"
    rejected: tuple[str, ...] = ()


def validate_config(raw: dict[str, Any]) -> tuple[dict[str, Any], tuple[str, ...]]:
    """Drop malformed values; return (clean, rejected_keys). Pure — no I/O.

    A bad config must not widen behavior (AC-K4): a non-numeric threshold or an
    empty model id is dropped so the caller's merge falls back to the last good
    value rather than a garbage one.
    """
    clean = dict(raw)
    rejected: list[str] = []
    if "amount_threshold" in clean:
        try:
            clean["amount_threshold"] = float(clean["amount_threshold"])
        except (TypeError, ValueError):
            del clean["amount_threshold"]
            rejected.append("amount_threshold")
    for key in _MODEL_ID_KEYS:
        if key in clean:
            value = clean[key]
            if not isinstance(value, str) or not value.strip():
                del clean[key]
                rejected.append(key)
    return clean, tuple(rejected)


class ConfigProvider:
    """Poll AppConfig for the current model-selection config.

    The caller re-invokes `get()` on its own cadence; "adopt a change within
    one poll interval" (AC-K3) is that next `get()` returning the new document.
    """

    def __init__(
        self,
        client: Any,
        *,
        application: str,
        environment: str,
        profile: str,
        fallback: dict[str, Any],
    ):
        self._client = client
        self._app = application
        self._env = environment
        self._profile = profile
        self._fallback = dict(fallback)
        self._token: str | None = None
        self._last_good: dict[str, Any] | None = None

    def get(self) -> ConfigResult:
        try:
            self._ensure_session()
            resp = self._client.get_latest_configuration(
                ConfigurationToken=self._token
            )
        except (ClientError, BotoCoreError) as exc:
            # AppConfig unreachable / throttled / refused → fail safe (AC-K1).
            # Data-API tokens are single-use and expire: drop the dead token so
            # the NEXT poll starts a fresh session instead of failing forever
            # on a warm Lambda (re-review #2). Log it — a permanent fallback
            # must be distinguishable from "no change" (e.g. AccessDenied from
            # a bad IAM grant).
            self._token = None
            _LOG.warning("appconfig poll failed (%s); serving %s",
                         type(exc).__name__,
                         "cache" if self._last_good is not None else "fallback")
            return self._fallback_result()

        self._token = resp.get("NextPollConfigurationToken", self._token)
        raw = resp.get("Configuration") or b""
        # appconfigdata Configuration is a blob (bytes); tolerate a streaming
        # wrapper across botocore versions.
        data = raw.read() if hasattr(raw, "read") else raw
        if not data:
            # AppConfig protocol: empty payload == unchanged since last poll.
            return self._cached_or_fallback()

        try:
            parsed = json.loads(data)
        except (ValueError, TypeError):
            return self._fallback_result()
        if not isinstance(parsed, dict):
            return self._fallback_result()

        clean, rejected = validate_config(parsed)
        # Fresh merge each poll (review #8): the bootstrap is the base, so a
        # key removed from the AppConfig document actually leaves the config.
        # A rejected key retains its last GOOD value, not the bootstrap (AC-K4).
        merged = {**self._fallback, **clean}
        if self._last_good is not None:
            for key in rejected:
                if key in self._last_good:
                    merged[key] = self._last_good[key]
        self._last_good = merged
        return ConfigResult(merged, "appconfig", rejected)

    def _ensure_session(self) -> None:
        if self._token is None:
            resp = self._client.start_configuration_session(
                ApplicationIdentifier=self._app,
                EnvironmentIdentifier=self._env,
                ConfigurationProfileIdentifier=self._profile,
            )
            self._token = resp["InitialConfigurationToken"]

    def _cached_or_fallback(self) -> ConfigResult:
        if self._last_good is not None:
            return ConfigResult(dict(self._last_good), "cache")
        return ConfigResult(dict(self._fallback), "fallback")

    def _fallback_result(self) -> ConfigResult:
        return self._cached_or_fallback()
