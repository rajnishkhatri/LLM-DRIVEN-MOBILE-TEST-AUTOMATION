"""contract-lint CLI.

Exit codes (spec C3, plan F1): 0 pass, 1 usage/internal error, 2 validation
failure. Subcommands: validate <target>, selftest.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from . import default_kernel_dir
from .report import canonical_dumps


class _Parser(argparse.ArgumentParser):
    """argparse defaults to exit 2 on usage errors; the C3 contract says 1."""

    def error(self, message: str):  # noqa: A003 - argparse API
        sys.stderr.write(f"{self.prog}: error: {message}\n")
        raise SystemExit(1)


def _build_parser() -> _Parser:
    parser = _Parser(prog="contract-lint", description=__doc__)
    sub = parser.add_subparsers(dest="cmd")
    validate = sub.add_parser("validate", help="validate a target file or directory")
    validate.add_argument("target")
    validate.add_argument("--kernel", help="kernel directory (schemas + corpus)")
    selftest = sub.add_parser("selftest", help="run the corpus self-test gate")
    selftest.add_argument("--kernel", help="kernel directory (schemas + corpus)")
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = _build_parser()
    try:
        args = parser.parse_args(argv)
    except SystemExit as exc:
        return int(exc.code or 0)
    if args.cmd is None:
        sys.stderr.write("contract-lint: error: a subcommand is required (validate | selftest)\n")
        return 1

    kernel_dir = Path(args.kernel).resolve() if args.kernel else default_kernel_dir()
    if not kernel_dir.is_dir():
        sys.stderr.write("contract-lint: error: kernel directory not found\n")
        return 1

    if args.cmd == "validate":
        target = Path(args.target)
        if not target.exists():
            sys.stderr.write("contract-lint: error: target does not exist\n")
            return 1
        from .registry import run_validate

        try:
            report = run_validate(target, kernel_dir)
        except Exception as exc:  # internal error is a usage-class failure, not a verdict
            sys.stderr.write(f"contract-lint: internal error: {type(exc).__name__}\n")
            return 1
        sys.stdout.write(canonical_dumps(report))
        return int(report["exit_code"])

    from .selftest import run_selftest

    try:
        report = run_selftest(kernel_dir)
    except Exception as exc:
        sys.stderr.write(f"contract-lint: internal error: {type(exc).__name__}\n")
        return 1
    sys.stdout.write(canonical_dumps(report))
    return int(report["exit_code"])


if __name__ == "__main__":
    raise SystemExit(main())
