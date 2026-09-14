"""Security helpers (import guardrails and value sanitisation).

Notably defends against spreadsheet formula injection: values coming from a
user-imported file that begin with a formula prefix (``=``, ``+``, ``-``,
``@``, tab, carriage return) are escaped so they cannot execute when a listing
or report is later opened in Excel/sheets. See plan section 18.4.
"""

from __future__ import annotations

_FORMULA_PREFIXES = ("=", "+", "-", "@", "\t", "\r")


def escape_formula_risk(value: str) -> str:
    """Escape a leading spreadsheet-formula prefix in ``value``.

    If ``value`` starts with a dangerous prefix, prepend a single quote so the
    cell is treated as text by spreadsheet applications. Otherwise returns the
    value unchanged.
    """
    if value.startswith(_FORMULA_PREFIXES):
        return "'" + value
    return value
