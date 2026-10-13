#!/usr/bin/env python3
"""Compatibility notice for a retired command that never evaluated extraction."""
import sys


def evaluate() -> int:
    print(
        "Not available: this retired command does not run financial extraction "
        "or calculate accuracy. Use the application's Evaluation Lab with an "
        "independently reviewed reference and the exact stored source hash. "
        "That workflow evaluates local text extraction only; it does not certify "
        "PDF/XBRL parsing, AI interpretation or financial approval.",
        file=sys.stderr,
    )
    return 2


if __name__ == "__main__":
    raise SystemExit(evaluate())
