"""Listing export formats (plan section 12.1: Markdown, JSON, CSV)."""

from __future__ import annotations

import csv
import io
import json
from typing import Any

from app.models.listing import ListingVersion


def _bullet_texts(listing: ListingVersion) -> list[str]:
    return [str(b.get("text", "")) for b in (listing.bullet_points or [])]


def export_json(listing: ListingVersion) -> str:
    payload: dict[str, Any] = {
        "id": str(listing.id),
        "project_id": str(listing.project_id),
        "product_id": str(listing.product_id),
        "marketplace": listing.marketplace,
        "locale": listing.locale,
        "title": listing.title,
        "bullet_points": listing.bullet_points or [],
        "description": listing.description,
        "search_terms": listing.search_terms,
        "model": listing.model,
        "prompt_version": listing.prompt_version,
        "input_snapshot_id": listing.input_snapshot_id,
        "status": listing.status,
        "fact_check": listing.fact_check,
        "rule_check": listing.rule_check,
    }
    return json.dumps(payload, ensure_ascii=False, indent=2)


def export_markdown(listing: ListingVersion) -> str:
    lines = [f"# {listing.title}", ""]
    bullets = _bullet_texts(listing)
    if bullets:
        lines += ["## Bullet points", ""]
        lines += [f"- {b}" for b in bullets]
        lines.append("")
    if listing.description:
        lines += ["## Description", "", listing.description, ""]
    if listing.search_terms:
        lines += ["## Search terms", "", listing.search_terms, ""]
    lines += [
        "## Checks",
        "",
        f"- Fact check passed: {bool((listing.fact_check or {}).get('passed'))}",
        f"- Rule check passed: {bool((listing.rule_check or {}).get('passed'))}",
        f"- Version: {listing.prompt_version} (snapshot {listing.input_snapshot_id})",
        "",
    ]
    return "\n".join(lines)


def export_csv(listing: ListingVersion) -> str:
    buffer = io.StringIO()
    writer = csv.writer(buffer)
    writer.writerow(["field", "value"])
    writer.writerow(["title", listing.title])
    for idx, bullet in enumerate(_bullet_texts(listing), start=1):
        writer.writerow([f"bullet_{idx}", bullet])
    writer.writerow(["description", listing.description or ""])
    writer.writerow(["search_terms", listing.search_terms or ""])
    return buffer.getvalue()


def export_listing(listing: ListingVersion, fmt: str) -> tuple[str, str, str]:
    """Return (content, media_type, filename_extension)."""
    if fmt == "json":
        return export_json(listing), "application/json", "json"
    if fmt == "csv":
        return export_csv(listing), "text/csv", "csv"
    if fmt == "markdown":
        return export_markdown(listing), "text/markdown", "md"
    raise ValueError(f"unsupported export format: {fmt}")
