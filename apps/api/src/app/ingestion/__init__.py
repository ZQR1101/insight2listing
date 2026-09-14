"""Data ingestion pipeline (plan section 8.4).

File parsing -> field mapping -> canonical normalisation -> deduplication ->
persistence + import report.
"""

from app.ingestion.adapters import (
    CSVAdapter,
    JSONAdapter,
    SourceAdapter,
    XLSXAdapter,
    adapter_for,
)
from app.ingestion.errors import (
    EmptyFileError,
    FileTooLargeError,
    MappingWarning,
    RowIssue,
    UnsupportedFileTypeError,
)

__all__ = [
    "CSVAdapter",
    "EmptyFileError",
    "FileTooLargeError",
    "JSONAdapter",
    "MappingWarning",
    "RowIssue",
    "SourceAdapter",
    "UnsupportedFileTypeError",
    "XLSXAdapter",
    "adapter_for",
]
