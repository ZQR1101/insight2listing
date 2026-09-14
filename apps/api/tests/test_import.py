"""Data import pipeline tests: CSV/JSON/XLSX, dedup, formula injection, errors."""

from __future__ import annotations

import csv
import io
import json

from httpx import AsyncClient

from conftest import create_project


def _products_csv(rows: list[dict]) -> bytes:
    buffer = io.StringIO()
    writer = csv.DictWriter(
        buffer,
        fieldnames=["external_id", "title", "brand", "price", "rating", "review_count"],
    )
    writer.writeheader()
    writer.writerows(rows)
    return buffer.getvalue().encode("utf-8")


def _products_json(rows: list[dict]) -> bytes:
    return json.dumps(rows).encode("utf-8")


def _products_xlsx(rows: list[dict]) -> bytes:
    from openpyxl import Workbook

    wb = Workbook()
    ws = wb.active
    ws.append(["external_id", "title", "brand", "price", "rating", "review_count"])
    for row in rows:
        ws.append(
            [
                row.get("external_id"),
                row.get("title"),
                row.get("brand"),
                row.get("price"),
                row.get("rating"),
                row.get("review_count"),
            ]
        )
    buffer = io.BytesIO()
    wb.save(buffer)
    return buffer.getvalue()


PRODUCT_ROWS = [
    {
        "external_id": "ASIN001",
        "title": "Compression Packing Cube Set",
        "brand": "PackRight",
        "price": "19.99",
        "rating": "4.5",
        "review_count": "1200",
    },
    {
        "external_id": "ASIN002",
        "title": "Glass Oil Sprayer Bottle",
        "brand": "Spritz",
        "price": "12.50",
        "rating": "4.2",
        "review_count": "860",
    },
]


async def _import(client: AsyncClient, project_id: str, filename: str, data: bytes, **form):
    return await client.post(
        f"/api/v1/projects/{project_id}/imports",
        files={"file": (filename, data)},
        data=form,
    )


async def test_import_products_csv(client: AsyncClient) -> None:
    project = await create_project(client)
    resp = await _import(
        client,
        project["id"],
        "products.csv",
        _products_csv(PRODUCT_ROWS),
        target="products",
        license="user_attested",
    )
    assert resp.status_code == 201, resp.text
    body = resp.json()
    assert body["status"] == "completed"
    assert body["report"]["imported"] == 2
    assert body["report"]["skipped_duplicates"] == 0
    # Project advanced from DRAFT to DATA_IMPORTED
    got = (await client.get(f"/api/v1/projects/{project['id']}")).json()
    assert got["status"] == "DATA_IMPORTED"

    products = (await client.get(f"/api/v1/projects/{project['id']}/products")).json()
    assert products["total"] == 2
    first = products["items"][0]
    assert first["rating"] == 4.5
    assert first["freshness"]["source"] == "user_upload"


async def test_import_products_json(client: AsyncClient) -> None:
    project = await create_project(client)
    resp = await _import(
        client, project["id"], "products.json", _products_json(PRODUCT_ROWS), target="products"
    )
    assert resp.status_code == 201, resp.text
    assert resp.json()["report"]["imported"] == 2


async def test_import_products_xlsx(client: AsyncClient) -> None:
    project = await create_project(client)
    resp = await _import(
        client, project["id"], "products.xlsx", _products_xlsx(PRODUCT_ROWS), target="products"
    )
    assert resp.status_code == 201, resp.text
    assert resp.json()["report"]["imported"] == 2


async def test_import_is_idempotent(client: AsyncClient) -> None:
    project = await create_project(client)
    data = _products_csv(PRODUCT_ROWS)
    first = await _import(client, project["id"], "products.csv", data, target="products")
    assert first.status_code == 201
    second = await _import(client, project["id"], "products.csv", data, target="products")
    assert second.status_code == 201
    assert second.json()["report"]["imported"] == 0
    assert second.json()["report"]["skipped_duplicates"] == 2
    products = (await client.get(f"/api/v1/projects/{project['id']}/products")).json()
    assert products["total"] == 2


async def test_formula_injection_is_escaped(client: AsyncClient) -> None:
    project = await create_project(client)
    rows = [
        {
            "external_id": "ASIN-X",
            "title": "=HYPERLINK(\"http://evil\", \"click\")",
            "brand": "=cmd|' /C calc'!A0",
            "price": "5.00",
            "rating": "1",
            "review_count": "1",
        }
    ]
    resp = await _import(
        client, project["id"], "products.csv", _products_csv(rows), target="products"
    )
    assert resp.status_code == 201, resp.text
    got = (await client.get(f"/api/v1/projects/{project['id']}/products")).json()
    item = got["items"][0]
    assert item["title"].startswith("'=HYPERLINK")
    assert item["brand"].startswith("'=cmd|")


async def test_invalid_row_reported_not_crashed(client: AsyncClient) -> None:
    project = await create_project(client)
    rows = [
        {"external_id": "OK1", "title": "Valid", "brand": "B", "price": "1", "rating": "5", "review_count": "1"},
        {"external_id": "BAD1", "title": "", "brand": "B", "price": "1", "rating": "5", "review_count": "1"},
    ]
    resp = await _import(
        client, project["id"], "products.csv", _products_csv(rows), target="products"
    )
    assert resp.status_code == 201, resp.text
    report = resp.json()["report"]
    assert report["imported"] == 1
    assert report["rows_invalid"] == 1
    assert any("row 2" in e for e in report["errors"])


async def test_unsupported_file_type(client: AsyncClient) -> None:
    project = await create_project(client)
    resp = await _import(
        client, project["id"], "products.txt", b"not a table", target="products"
    )
    assert resp.status_code == 201, resp.text
    body = resp.json()
    assert body["status"] == "failed"
    assert any("unsupported file type" in e for e in body["report"]["errors"])


async def test_preview_detects_columns(client: AsyncClient) -> None:
    project = await create_project(client)
    resp = await client.post(
        f"/api/v1/projects/{project['id']}/imports/preview",
        files={"file": ("products.csv", _products_csv(PRODUCT_ROWS))},
        data={"target": "products"},
    )
    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert body["row_count"] == 2
    targets = {c["detected_target"] for c in body["columns"]}
    assert {"title", "price", "external_id"} <= targets


async def test_import_reviews_link_to_products(client: AsyncClient) -> None:
    project = await create_project(client)
    await _import(
        client, project["id"], "products.csv", _products_csv(PRODUCT_ROWS), target="products"
    )

    reviews_csv = csv_dump(
        [
            {"product_external_id": "ASIN001", "rating": "1", "body": "zipper broke after a week"},
            {"product_external_id": "ASIN002", "rating": "5", "body": "love the fine mist"},
            {"product_external_id": "ASIN999", "rating": "3", "body": "unlinked product review"},
        ]
    )
    resp = await _import(
        client, project["id"], "reviews.csv", reviews_csv, target="reviews"
    )
    assert resp.status_code == 201, resp.text
    assert resp.json()["report"]["imported"] == 3

    reviews = (await client.get(f"/api/v1/projects/{project['id']}/reviews")).json()
    assert reviews["total"] == 3
    by_body = {r["body"]: r for r in reviews["items"]}
    assert by_body["zipper broke after a week"]["product_id"] is not None
    assert by_body["unlinked product review"]["product_id"] is None


async def test_review_dedup_by_content(client: AsyncClient) -> None:
    project = await create_project(client)
    data = csv_dump(
        [
            {"product_external_id": "ASIN001", "rating": "1", "body": "same complaint"},
            {"product_external_id": "ASIN001", "rating": "1", "body": "same complaint"},
        ]
    )
    resp = await _import(client, project["id"], "reviews.csv", data, target="reviews")
    assert resp.status_code == 201
    report = resp.json()["report"]
    assert report["imported"] == 1
    assert report["skipped_duplicates"] == 1


async def test_review_search(client: AsyncClient) -> None:
    project = await create_project(client)
    data = csv_dump(
        [
            {"product_external_id": "ASIN001", "rating": "1", "body": "the zipper is flimsy"},
            {"product_external_id": "ASIN001", "rating": "5", "body": "great value"},
        ]
    )
    await _import(client, project["id"], "reviews.csv", data, target="reviews")
    resp = await client.get(
        f"/api/v1/projects/{project['id']}/reviews", params={"q": "zipper"}
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["total"] == 1
    assert body["items"][0]["body"].startswith("the zipper")


def csv_dump(rows: list[dict]) -> bytes:
    fields = list(rows[0].keys())
    buffer = io.StringIO()
    writer = csv.DictWriter(buffer, fieldnames=fields)
    writer.writeheader()
    writer.writerows(rows)
    return buffer.getvalue().encode("utf-8")


async def test_import_records_source_and_audit(client: AsyncClient, engine) -> None:
    from sqlalchemy import func, select
    from sqlalchemy.ext.asyncio import AsyncSession

    from app.models.audit import AuditEvent
    from app.models.source import SourceRecord

    project = await create_project(client)
    await _import(
        client, project["id"], "products.csv", _products_csv(PRODUCT_ROWS), target="products"
    )
    async with AsyncSession(engine) as session:
        sources = (await session.execute(select(func.count()).select_from(SourceRecord))).scalar_one()
        audits = (await session.execute(select(func.count()).select_from(AuditEvent))).scalar_one()
    assert sources == 1
    assert audits >= 1  # project.created + import.completed + maybe status change
