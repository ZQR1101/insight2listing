"""File adapters (plan section 8.4).

Each adapter reads bytes in one source format and yields rows as dicts keyed
by the original column names. It is the only layer that understands a specific
file format. Validations in :mod:`app.ingestion.validation` normalise values
and apply formula-injection protection.
"""

from __future__ import annotations

import csv
import io
import json
from abc import ABC, abstractmethod
from typing import Any

from app.core.security import escape_formula_risk
from app.ingestion.errors import EmptyFileError, FileTooLargeError, UnsupportedFileTypeError


def _sanitise(value: Any) -> Any:
    """Neutralise formula-injection prefixes in string cells (plan 18.4)."""
    if isinstance(value, str):
        return escape_formula_risk(value)
    return value


class SourceAdapter(ABC):
    """Base adapter: turns file bytes plus a target name into rows."""

    supported_extensions: tuple[str, ...] = ()

    def __init__(self, *, max_bytes: int) -> None:
        self.max_bytes = max_bytes

    def validate_size(self, data: bytes) -> None:
        if len(data) > self.max_bytes:
            raise FileTooLargeError(
                f"file exceeds size limit of {self.max_bytes} bytes"
            )

    @abstractmethod
    def read(self, data: bytes) -> list[dict[str, Any]]:
        raise NotImplementedError


class CSVAdapter(SourceAdapter):
    supported_extensions = (".csv",)

    def read(self, data: bytes) -> list[dict[str, Any]]:
        self.validate_size(data)
        text = data.decode("utf-8-sig")
        reader = csv.DictReader(io.StringIO(text))
        rows: list[dict[str, Any]] = []
        for raw in reader:
            row = {k: _sanitise(v) for k, v in raw.items()}
            rows.append(row)
        if not rows:
            raise EmptyFileError("no data rows found in CSV")
        return rows


class JSONAdapter(SourceAdapter):
    supported_extensions = (".json",)

    def read(self, data: bytes) -> list[dict[str, Any]]:
        self.validate_size(data)
        payload = json.loads(data.decode("utf-8-sig"))
        if isinstance(payload, dict):
            # Accept {"data": [...]} or a single record object.
            for value in payload.values():
                if isinstance(value, list) and value and isinstance(value[0], dict):
                    payload = value
                    break
            else:
                payload = [payload]
        if not isinstance(payload, list):
            raise ValueError("JSON payload must be a list of records or an object with a list")
        if not payload:
            raise EmptyFileError("no data rows found in JSON")
        return [{k: _sanitise(v) for k, v in row.items()} for row in payload]


class XLSXAdapter(SourceAdapter):
    supported_extensions = (".xlsx", ".xlsm")

    def read(self, data: bytes) -> list[dict[str, Any]]:
        self.validate_size(data)
        from openpyxl import load_workbook  # type: ignore[import-untyped]

        wb = load_workbook(io.BytesIO(data), read_only=True, data_only=True)
        ws = wb.active
        if ws is None:
            raise EmptyFileError("workbook has no active sheet")
        rows_iter = ws.iter_rows(values_only=True)
        header: tuple[Any, ...] | None = next(rows_iter, None)
        if header is None:
            raise EmptyFileError("workbook is empty")
        headers = [str(h).strip() if h is not None else "" for h in header]
        rows: list[dict[str, Any]] = []
        for values in rows_iter:
            row = {headers[i]: _sanitise(values[i]) for i in range(len(headers))}
            rows.append(row)
        wb.close()
        if not rows:
            raise EmptyFileError("no data rows found in XLSX")
        return rows


def adapter_for(filename: str, *, max_bytes: int) -> SourceAdapter:
    """Resolve the adapter for a file name, by extension."""
    lowered = filename.lower()
    for adapter_cls in (CSVAdapter, JSONAdapter, XLSXAdapter):
        if lowered.endswith(adapter_cls.supported_extensions):
            return adapter_cls(max_bytes=max_bytes)
    ext = lowered.rsplit(".", 1)[-1] if "." in lowered else "(none)"
    raise UnsupportedFileTypeError(f"unsupported file type: .{ext}")
