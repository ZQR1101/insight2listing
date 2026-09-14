"""Import pipeline errors.

Row-level problems are collected and reported without aborting the whole
import (plan sections 6.2, 8.4). A :class:`RowIssue` is one problem attached to
one source row.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(slots=True)
class RowIssue:
    row_number: int  # 1-based position in the source file
    issue: str
    field: str | None = None
    value: Any = None
    severity: str = "error"  # "error" or "warning"


class UnsupportedFileTypeError(Exception):
    """Raised when the uploaded file type cannot be parsed."""


class FileTooLargeError(Exception):
    """Raised when the uploaded file exceeds the configured size limit."""


class EmptyFileError(Exception):
    """Raised when the uploaded file has no data rows."""


class MappingWarning(Exception):
    """Raised when a canonical field is not supplied and no synonym matches."""
