"""End-to-end Listing workbench API tests (Phase D)."""

from __future__ import annotations

import csv
import io

import httpx
import pytest_asyncio

from conftest import create_project


def _csv(rows: list[dict], fieldnames: list[str]) -> bytes:
    buf = io.StringIO()
    w = csv.DictWriter(buf, fieldnames=fieldnames)
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
async def ready_project(client: httpx.AsyncClient) -> dict:
    """Project with product, accepted insight and confirmed facts (ready to list)."""
    project = await create_project(client, name="Listing Project")
    pid = project["id"]

    products = _csv(
        [{"external_id": "S1", "title": "Glass Oil Sprayer", "brand": "Spritz"}],
        ["external_id", "title", "brand"],
    )
    resp = await _import(client, pid, "products.csv", products, "products")
    assert resp.status_code == 201, resp.text

    reviews = _csv(
        [
            {"product_external_id": "S1", "rating": "1", "body": "the gasket leaks oil"},
            {"product_external_id": "S1", "rating": "1", "body": "gasket leaks after use"},
            {"product_external_id": "S1", "rating": "5", "body": "nice fine mist spray"},
        ],
        ["product_external_id", "rating", "body"],
    )
    resp = await _import(client, pid, "reviews.csv", reviews, "reviews")
    assert resp.status_code == 201, resp.text

    resp = await client.post(f"/api/v1/projects/{pid}/insights/generate")
    assert resp.status_code == 200, resp.text
    insights = (await client.get(f"/api/v1/projects/{pid}/insights")).json()["items"]
    gasket = next(i for i in insights if i["topic"] == "gasket")
    resp = await client.patch(
        f"/api/v1/projects/{pid}/insights/{gasket['id']}/status",
        json={"status": "accepted"},
    )
    assert resp.status_code == 200, resp.text

    product_id = (await client.get(f"/api/v1/projects/{pid}/products")).json()["items"][0]["id"]
    facts = [
        {"fact_type": "material", "value": "silicone gasket seal"},
        {"fact_type": "capacity", "value": "200", "unit": "ml"},
        {"fact_type": "usage_limitation", "value": "hand wash only"},
    ]
    fact_ids = []
    for payload in facts:
        resp = await client.post(
            f"/api/v1/projects/{pid}/products/{product_id}/facts", json=payload
        )
        assert resp.status_code == 201, resp.text
        fact_ids.append(resp.json()["id"])
    for fid in fact_ids:
        resp = await client.patch(
            f"/api/v1/projects/{pid}/facts/{fid}/status", json={"status": "user_confirmed"}
        )
        assert resp.status_code == 200, resp.text

    return {"project": project, "product_id": product_id, "fact_ids": fact_ids}


async def test_generate_listing_is_fact_bound(client, ready_project) -> None:
    pid = ready_project["project"]["id"]
    resp = await client.post(
        f"/api/v1/projects/{pid}/products/{ready_project['product_id']}/listings/generate"
    )
    assert resp.status_code == 201, resp.text
    listing = resp.json()

    assert listing["status"] == "draft"
    assert listing["model"] == "rule-template-v1"
    assert listing["fact_check"]["passed"] is True
    assert listing["rule_check"]["passed"] is True
    assert "silicone gasket seal" in listing["title"]

    bullets = listing["bullet_points"]
    assert 1 <= len(bullets) <= 5
    gasket_bullets = [
        b
        for b in bullets
        if b["fact_ids"] and b["insight_ids"]
    ]
    assert gasket_bullets, "expected a traceable pain-point bullet"
    assert "gasket" in gasket_bullets[0]["text"].lower()

    texts = " ".join(b["text"] for b in bullets)
    assert "200 ml" in texts
    assert "hand wash only" in texts

    project = (await client.get(f"/api/v1/projects/{pid}")).json()
    assert project["status"] == "LISTING_GENERATED"


async def test_generate_without_confirmed_facts_is_422(client) -> None:
    project = await create_project(client, name="No Facts")
    products = _csv(
        [{"external_id": "S1", "title": "Glass Oil Sprayer", "brand": "Spritz"}],
        ["external_id", "title", "brand"],
    )
    await _import(client, project["id"], "products.csv", products, "products")
    product_id = (await client.get(f"/api/v1/projects/{project['id']}/products")).json()["items"][0]["id"]

    resp = await client.post(
        f"/api/v1/projects/{project['id']}/products/{product_id}/listings/generate"
    )
    assert resp.status_code == 422
    assert "confirmed facts" in resp.json()["detail"]


async def test_approve_then_regenerate_keeps_approved_version(client, ready_project) -> None:
    pid = ready_project["project"]["id"]
    product_id = ready_project["product_id"]
    first = (
        await client.post(f"/api/v1/projects/{pid}/products/{product_id}/listings/generate")
    ).json()

    resp = await client.post(f"/api/v1/projects/{pid}/listings/{first['id']}/approve")
    assert resp.status_code == 200, resp.text
    assert resp.json()["status"] == "approved"

    second = (
        await client.post(f"/api/v1/projects/{pid}/products/{product_id}/listings/generate")
    ).json()
    assert second["id"] != first["id"]

    old = (await client.get(f"/api/v1/projects/{pid}/listings/{first['id']}")).json()
    assert old["status"] == "approved"


async def test_edit_with_forbidden_claim_blocks_approval(client, ready_project) -> None:
    pid = ready_project["project"]["id"]
    product_id = ready_project["product_id"]
    listing = (
        await client.post(f"/api/v1/projects/{pid}/products/{product_id}/listings/generate")
    ).json()

    resp = await client.patch(
        f"/api/v1/projects/{pid}/listings/{listing['id']}",
        json={"title": f"{listing['title']} - the best ever"},
    )
    assert resp.status_code == 200
    assert resp.json()["status"] == "draft"

    approve = await client.post(f"/api/v1/projects/{pid}/listings/{listing['id']}/approve")
    assert approve.status_code == 422
    assert "best" in approve.json()["detail"]


async def test_export_formats(client, ready_project) -> None:
    pid = ready_project["project"]["id"]
    product_id = ready_project["product_id"]
    listing = (
        await client.post(f"/api/v1/projects/{pid}/products/{product_id}/listings/generate")
    ).json()

    for fmt, marker in (("json", '"title"'), ("markdown", "# "), ("csv", "title,")):
        resp = await client.get(
            f"/api/v1/projects/{pid}/listings/{listing['id']}/export", params={"format": fmt}
        )
        assert resp.status_code == 200, resp.text
        assert len(resp.content) > 0
        assert marker in resp.text

    bad = await client.get(
        f"/api/v1/projects/{pid}/listings/{listing['id']}/export", params={"format": "docx"}
    )
    assert bad.status_code == 422
