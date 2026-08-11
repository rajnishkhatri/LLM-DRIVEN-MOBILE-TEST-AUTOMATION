"""Reference implementation of contract-lint + gate-wrap + gate-runner +
write-guard + role-emit for the SDD role kernel.

The golden corpus + CHK table is the normative contract (spec C3), extended at
build item 2 with golden runs (ADR 0002); this package is the replaceable
reference implementation. Exit codes: 0 = pass, 1 = usage/internal error,
2 = validation failure / run failed.
"""

from pathlib import Path

__version__ = "0.7.4"

VALIDATOR_VERSION = __version__


def default_kernel_dir() -> Path:
    """Resolve the sibling kernel/ directory from the installed package location."""
    return Path(__file__).resolve().parents[3] / "kernel"
