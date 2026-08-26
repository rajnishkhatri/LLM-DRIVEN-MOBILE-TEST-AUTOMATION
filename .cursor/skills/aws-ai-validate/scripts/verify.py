#!/usr/bin/env python3
"""Offline verification harness runner for the aws-ai-* family.

This is the "actually run it" proof for the AWS-AI capability workflow. It
discovers and runs the pytest suite under ``./tests`` (botocore Stubber contract
tests for ``bedrock-runtime`` / ``sagemaker-runtime`` + moto tests for the
supporting infra and SageMaker control plane), prints a concise PASS/FAIL
summary, and exits non-zero on any failure.

The gated-online contract
--------------------------
The harness is **offline by design**. It will not permit a real AWS call unless
BOTH conditions hold:

  1. the ``--online`` flag is passed, AND
  2. the environment variable ``AWS_AI_ALLOW_ONLINE=1`` is set.

Either alone is ignored and the run stays offline (with a warning). This double
latch mirrors the family rule: no real AWS call happens outside the deliberately
gated ``aws-ai-validate`` real-path, and nothing that can incur cost runs without
an explicit human opt-in.

In offline mode the child pytest process is launched with a scrubbed environment
— any ambient ``AWS_PROFILE`` / access keys are removed, bogus static
credentials are injected, and IMDS is disabled — so that even a mis-written test
physically cannot reach a real account: it fails signing or endpoint resolution
instead. moto and the botocore Stubber both operate entirely in-process, so the
whole default suite runs with no network and no credentials.

Only the Python standard library is used here (``argparse``, ``os``,
``subprocess``, ``sys``, ``pathlib``); pytest is invoked as a subprocess so the
runner has no import-time dependency on it.

Usage
-----
    python verify.py                 # offline (default) — Stubber + moto, no AWS
    python verify.py -k converse     # pass extra args straight through to pytest
    AWS_AI_ALLOW_ONLINE=1 python verify.py --online   # gated real-AWS path
"""
from __future__ import annotations

import argparse
import os
import subprocess
import sys
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
TESTS_DIR = SCRIPT_DIR / "tests"

ONLINE_ENV_LATCH = "AWS_AI_ALLOW_ONLINE"

# AWS-related environment keys scrubbed before an offline run so nothing can
# resolve to a real account.
_AWS_ENV_KEYS = (
    "AWS_PROFILE",
    "AWS_DEFAULT_PROFILE",
    "AWS_ACCESS_KEY_ID",
    "AWS_SECRET_ACCESS_KEY",
    "AWS_SESSION_TOKEN",
    "AWS_SECURITY_TOKEN",
    "AWS_BEARER_TOKEN_BEDROCK",
    "AWS_ROLE_ARN",
    "AWS_WEB_IDENTITY_TOKEN_FILE",
    "AWS_ENDPOINT_URL",
)


def _parse_args(argv):
    parser = argparse.ArgumentParser(
        prog="verify.py",
        description="Run the aws-ai-* offline verification harness (Stubber + moto).",
    )
    parser.add_argument(
        "--online",
        action="store_true",
        help=(
            "Attempt the gated real-AWS path. Only honored when the environment "
            f"variable {ONLINE_ENV_LATCH}=1 is ALSO set; otherwise the run stays "
            "offline."
        ),
    )
    # Unrecognized args (e.g. -k, -v, a test path) are forwarded to pytest.
    args, pytest_args = parser.parse_known_args(argv)
    args.pytest_args = pytest_args
    return args


def _online_permitted(flag_online: bool) -> bool:
    """The double latch: both the flag and the env var are required."""
    env_ok = os.environ.get(ONLINE_ENV_LATCH) == "1"
    return bool(flag_online) and env_ok


def _build_child_env(online: bool) -> dict:
    env = dict(os.environ)
    # The harness suite needs zero pytest plugins. Disable setuptools-entrypoint
    # plugin autoload so a broken third-party plugin living in an ambient or
    # shared interpreter (e.g. a stray logfire / opentelemetry pytest plugin)
    # cannot abort collection before our own tests run. This keeps the offline
    # gate runnable in any interpreter, not just a clean venv.
    env["PYTEST_DISABLE_PLUGIN_AUTOLOAD"] = "1"
    if online:
        # Real-path: pass the caller's credentials/region through untouched.
        return env
    # Offline: neutralize every credential source so a real call is impossible.
    for key in _AWS_ENV_KEYS:
        env.pop(key, None)
    env["AWS_ACCESS_KEY_ID"] = "testing"
    env["AWS_SECRET_ACCESS_KEY"] = "testing"
    env["AWS_SESSION_TOKEN"] = "testing"
    env["AWS_SECURITY_TOKEN"] = "testing"
    env.setdefault("AWS_DEFAULT_REGION", "us-east-1")
    # Block the instance-metadata credential fallback outright.
    env["AWS_EC2_METADATA_DISABLED"] = "true"
    env["AWS_AI_HARNESS_MODE"] = "offline"
    return env


def main(argv=None) -> int:
    args = _parse_args(sys.argv[1:] if argv is None else argv)

    if not TESTS_DIR.is_dir():
        print(f"error: no tests directory at {TESTS_DIR}", file=sys.stderr)
        return 2

    requested_online = args.online
    online = _online_permitted(requested_online)

    if requested_online and not online:
        print(
            "warning: --online was passed but "
            f"{ONLINE_ENV_LATCH}=1 is not set; staying OFFLINE.",
            file=sys.stderr,
        )

    mode = "ONLINE (gated real-AWS)" if online else "OFFLINE (Stubber + moto, no AWS)"
    print("=" * 68)
    print(f"aws-ai verification harness  |  mode: {mode}")
    print(f"tests: {TESTS_DIR}")
    print("=" * 68, flush=True)

    if online:
        print(
            "!! Real AWS credentials are in scope for this run. Real calls may\n"
            "!! incur cost and require explicit human approval per the family\n"
            "!! constraints. Proceeding because both latches are set.",
            flush=True,
        )

    cmd = [sys.executable, "-m", "pytest", str(TESTS_DIR), "-q"]
    # Forward extra args, dropping a leading "--" separator argparse leaves in.
    extra = [a for a in args.pytest_args if a != "--"]
    cmd.extend(extra)

    child_env = _build_child_env(online)
    completed = subprocess.run(cmd, env=child_env)

    print("-" * 68)
    if completed.returncode == 0:
        print(f"RESULT: PASS  ({mode})")
    else:
        print(f"RESULT: FAIL  (pytest exit {completed.returncode}, {mode})")
    print("-" * 68, flush=True)
    return completed.returncode


if __name__ == "__main__":
    raise SystemExit(main())
