"""Security guardrail unit tests."""

from __future__ import annotations

from app.core.security import escape_formula_risk


def test_formula_prefixes_are_escaped() -> None:
    for prefix in ("=", "+", "-", "@", "\t", "\r"):
        assert escape_formula_risk(f"{prefix}cmd") == f"'{prefix}cmd"


def test_safe_values_unchanged() -> None:
    for value in ("hello", "4.2", "glass oil sprayer", "", "   ", "total: 12"):
        assert escape_formula_risk(value) == value


def test_already_escaped_not_double_escaped() -> None:
    assert escape_formula_risk("'=SUM(A1)") == "'=SUM(A1)"
