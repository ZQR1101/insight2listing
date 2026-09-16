"""End-to-end insight / opportunity-card API tests (Phase C)."""

from __future__ import annotations

import httpx
import pytest_asyncio

from conftest import create_project


def _products(rows: list[dict]) -> bytes:
    import csv
    import io

    buf = io.StringIO()
    w = csv.DictWriter(buf, fieldnames=["external_id", "title", "brand"])
    w.writeheader()
    w.writerows(rows)
    return buf.getvalue().encode("utf-8")


def _reviews(rows: list[dict]) -> bytes:
    import csv
    import io

    buf = io.StringIO()
    w = csv.DictWriter(buf, fieldnames=["product_external_id", "rating", "body"])
    w.writeheader()
    w.writerows(rows)
    return buf.getvalue().encode("utf-8")


async def _import(client: httpx.AsyncClient, pid: str, filename: str, data: bytes, target: str):
    return await client.post(
        f"/api/v1/projects/{pid}/imports",
        files={"file": (filename, data)},
        data={"target": target},
    )


@pytest_asyncio.fixture
async def prepared_project(client: httpx.AsyncClient) -> dict:
    project = await create_project(client, name="Sprayer Insights")
    pid = project["id"]
    await _import(
        client,
        pid,
        "products.csv",
        _products([{"external_id": "S1", "title": "Glass Oil Sprayer", "brand": "Spritz"}]),
        "products",
    )
    reviews = _reviews(
        [
            {"product_external_id": "S1", "rating": "1", "body": "the nozzle leaks oil everywhere"},
            {"product_external_id": "S1", "rating": "1", "body": "nozzle leaks after a week"},
            {"product_external_id": "S1", "rating": "2", "body": "it leaks oil when stored"},
            {"product_external_id": "S1", "rating": "5", "body": "great fine mist control"},
            {"product_external_id": "S1", "rating": "5", "body": "love the fine mist"},
            {"product_external_id": "S1", "rating": "4", "body": "mist is very even"},
        ]
    )
    resp = await _import(client, pid, "reviews.csv", reviews, "reviews")
    assert resp.status_code == 201, resp.text
    return project


async def test_generate_insights_and_advance_status(client, prepared_project) -> None:
    pid = prepared_project["id"]
    resp = await client.post(f"/api/v1/projects/{pid}/insights/generate")
    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert body["insights"] > 0
    assert body["cards"] >= 1
    assert body["reviews_skipped"] == 0

    proj = (await client.get(f"/api/v1/projects/{pid}")).json()
    assert proj["status"] == "INSIGHTS_GENERATED"


async def test_generate_is_idempotent_guard(client, prepared_project) -> None:
    pid = prepared_project["id"]
    assert (await client.post(f"/api/v1/projects/{pid}/insights/generate")).status_code == 200
    again = await client.post(f"/api/v1/projects/{pid}/insights/generate")
    assert again.status_code == 409


async def test_list_and_detail_with_evidence(client, prepared_project) -> None:
    pid = prepared_project["id"]
    await client.post(f"/api/v1/projects/{pid}/insights/generate")

    listed = (await client.get(f"/api/v1/projects/{pid}/insights")).json()
    assert listed["total"] > 0
    topics = [i["topic"] for i in listed["items"]]
    assert len(topics) == len(set(topics))

    detail = (await client.get(f"/api/v1/projects/{pid}/insights/{listed['items'][0]['id']}")).json()
    assert detail["status"] == "generated"
    assert len(detail["evidence"]) >= 1
    assert detail["evidence"][0]["excerpt"] != ""


async def test_accept_insight_reviews_and_advances(client, prepared_project) -> None:
    pid = prepared_project["id"]
    await client.post(f"/api/v1/projects/{pid}/insights/generate")
    item = (await client.get(f"/api/v1/projects/{pid}/insights")).json()["items"][0]
    iid = item["id"]

    resp = await client.patch(
        f"/api/v1/projects/{pid}/insights/{iid}/status", json={"status": "accepted"}
    )
    assert resp.status_code == 200
    assert resp.json()["status"] == "accepted"

    proj = (await client.get(f"/api/v1/projects/{pid}")).json()
    assert proj["status"] == "INSIGHTS_REVIEWED"


async def test_edit_insight_sets_edited(client, prepared_project) -> None:
    pid = prepared_project["id"]
    await client.post(f"/api/v1/projects/{pid}/insights/generate")
    iid = (await client.get(f"/api/v1/projects/{pid}/insights")).json()["items"][0]["id"]

    resp = await client.patch(
        f"/api/v1/projects/{pid}/insights/{iid}",
        json={"summary": "edited summary"},
    )
    assert resp.status_code == 200
    assert resp.json()["status"] == "edited"
    assert resp.json()["summary"] == "edited summary"


async def test_opportunity_card_has_missing_dimensions(client, prepared_project) -> None:
    pid = prepared_project["id"]
    await client.post(f"/api/v1/projects/{pid}/insights/generate")

    cards = (await client.get(f"/api/v1/projects/{pid}/opportunity-cards")).json()
    assert cards["total"] >= 1
    card = cards["items"][0]
    assert card["score_version"] == "opportunity-v1"
    assert card["opportunity_score"] is not None or card["confidence"] is not None
    assert "supplier_cost" in (card["missing_dimensions"] or [])
    assert "demand" in (card["missing_dimensions"] or [])

    # Filter by product works via the product-id endpoint.
    pid_card = (await client.get(f"/api/v1/projects/{pid}/opportunity-cards/{card['product_id']}")).json()
    assert pid_card["id"] == card["id"]


async def test_generate_no_op_without_reviews(client) -> None:
    project = await create_project(client, name="Empty")
    resp = await client.post(f"/api/v1/projects/{project['id']}/insights/generate")
    assert resp.status_code == 200
    body = resp.json()
    assert body["insights"] == 0
    assert body["cards"] == 0
    proj = (await client.get(f"/api/v1/projects/{project['id']}")).json()
    assert proj["status"] == "DRAFT"
