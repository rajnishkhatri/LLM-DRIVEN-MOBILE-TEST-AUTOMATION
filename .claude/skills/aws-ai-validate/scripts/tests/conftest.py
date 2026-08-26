"""Shared pytest fixtures / network backstop for the offline harness.

Offline is the default and must be enforced at the *network* layer, not just by
convention: a forgotten Stubber or an un-mocked call must become a loud error,
never a silent real request (and possible bill).

Why not ``pytest-socket``
-------------------------
The obvious tool is ``pytest-socket --disable-socket``, but it blocks at
*socket creation* (and ``gethostbyname``), which is too coarse for botocore:
botocore resolves the endpoint hostname while *preparing* a request — before the
Stubber/moto short-circuit — so a blanket socket block makes even fully mocked
tests fail on DNS. We instead block real outbound **connects** (what actually
costs money) and leave socket creation + DNS alone. Under Stubber and
``@mock_aws`` no real connect happens (the HTTP send is intercepted), so mocked
tests pass; a genuinely leaked call reaches ``create_connection`` and raises.

The gated online smoke (``verify.py --online`` with ``AWS_AI_ALLOW_ONLINE=1``)
needs the network, so the guard is lifted there. Belt-and-suspenders: ``verify.py``
also scrubs credentials and injects bogus static keys, so even a leaked call that
somehow connected would fail signing rather than bill an account.
"""
import os
import socket

_ALLOWED_HOSTS = {"127.0.0.1", "::1", "localhost"}


def _online_allowed() -> bool:
    return os.environ.get("AWS_AI_ALLOW_ONLINE") == "1"


def pytest_configure(config):
    if _online_allowed():
        return

    real_create_connection = socket.create_connection

    def guarded_create_connection(address, *args, **kwargs):
        host = address[0] if isinstance(address, (tuple, list)) else address
        if host in _ALLOWED_HOSTS:
            return real_create_connection(address, *args, **kwargs)
        raise RuntimeError(
            f"Offline harness blocked a real outbound connect to {host!r}: a "
            "Stubber or moto mock is missing. No real AWS call is allowed offline "
            "(run the gated `verify.py --online` path for real access)."
        )

    socket.create_connection = guarded_create_connection
