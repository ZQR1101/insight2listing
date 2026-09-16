"""End-to-end product facts centre API tests (Phase D)."""

from __future__ import annotations

import csv
import io

import httpx
import pytest_asyncio

from conftest import create_project


def _products_csv(rows: list[dict]) -> bytes:
    buf = io.StringIO()
    w = csv.DictWriter(buf, fieldnames=["external_id", "title", "brand"])
    w.writeheader()
    w.writerows(rows)
    return buf.getvalue().encode("utf-8")


@pytest_asyncio.fixture
async def project_with_product(client: httpx.AsyncClient) -> dict:
    project = await create_project(client, name="Facts Project")
    resp = await client.post(
        f"/api/v1/projects/{project['id']}/imports",
        files={
            "file": (
                "products.csv",
                _products_csv(
                    [{"external_id": "S1", "title": "Glass Oil Sprayer", "brand": "Spritz"}]
                ),
            )
        },
        data={"target": "products"},
    )
    assert resp.status_code == 201, resp.text
    product = (await client.get(f"/api/v1/projects/{project['id']}/products")).json()["items"][0]
    return {"project": project, "product": product}


async def _create_fact(client: httpx.AsyncClient, pid: str, product_id: str, **payload) -> httpx.Response:
    body = {"fact_type": "material", "value": "borosilicate glass", **payload}
    return await client.post(
        f"/api/v1/projects/{pid}/products/{product_id}/facts", json=body
    )


async def test_create_fact_is_unverified(client, project_with_product) -> None:
    pid = project_with_product["project"]["id"]
    product_id = project_with_product["product"]["id"]
    resp = await _create_fact(client, pid, product_id)
    assert resp.status_code == 201, resp.text
    body = resp.json()
    assert body["verification_status"] == "unverified"
    assert body["verified_by"] is None
    assert body["verified_at"] is None


async def test_confirm_stamp_verified_by_and_at(client, project_with_product) -> None:
    pid = project_with_product["project"]["id"]
    product_id = project_with_product["product"]["id"]
    fact_id = (await _create_fact(client, pid, product_id)).json()["id"]

    resp = await client.patch(
        f"/api/v1/projects/{pid}/facts/{fact_id}/status",
        json={"status": "user_confirmed"},
        headers={"X-Actor": "tester"},
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["verification_status"] == "user_confirmed"
    assert body["verified_by"] == "tester"
    assert body["verified_at"] is not None


async def test_invalid_status_rejected(client, project_with_product) -> None:
    pid = project_with_product["project"]["id"]
    product_id = project_with_product["product"]["id"]
    fact_id = (await _create_fact(client, pid, product_id)).json()["id"]
    resp = await client.patch(
        f"/api/v1/projects/{pid}/facts/{fact_id}/status",
        json={"status": "expired"},
    )
    assert resp.status_code == 422


async def test_confirm_gate_requires_confirmed_fact(client, project_with_product) -> None:
    pid = project_with_product["project"]["id"]
    product_id = project_with_product["product"]["id"]
    await _create_fact(client, pid, product_id)  # stays unverified

    resp = await client.post(f"/api/v1/projects/{pid}/facts/confirm")
    assert resp.status_code == 409
    project = (await client.get(f"/api/v1/projects/{pid}")).json()
    assert project["status"] != "PRODUCT_FACTS_CONFIRMED"


async def test_confirm_gate_advances_workflow(client, project_with_product) -> None:
    pid = project_with_product["project"]["id"]
    product_id = project_with_product["product"]["id"]
    fact_id = (await _create_fact(client, pid, product_id)).json()["id"]
    await client.patch(
        f"/api/v1/projects/{pid}/facts/{fact_id}/status",
        json={"status": "user_confirmed"},
    )

    resp = await client.post(f"/api/v1/projects/{pid}/facts/confirm")
    assert resp.status_code == 200, resp.text
    assert resp.json()["status"] == "PRODUCT_FACTS_CONFIRMED"
    assert resp.json()["confirmed_facts"] >= 1


async def test_list_filter_by_status_and_delete(client, project_with_product) -> None:
    pid = project_with_product["project"]["id"]
    product_id = project_with_product["product"]["id"]
    f1 = (await _create_fact(client, pid, product_id)).json()["id"]
    await _create_fact(client, pid, product_id, fact_type="capacity", value="200", unit="ml")

    listed = (await client.get(f"/api/v1/projects/{pid}/facts")).json()
    assert listed["total"] == 2

    await client.patch(
        f"/api/v1/projects/{pid}/facts/{f1}/status", json={"status": "user_confirmed"}
    )
    confirmed = (
        await client.get(f"/api/v1/projects/{pid}/facts", params={"fact_status": "user_confirmed"})
    ).json()
    assert confirmed["total"] == 1

    resp = await client.delete(f"/api/v1/projects/{pid}/facts/{f1}")
    assert resp.status_code == 204
    assert (await client.get(f"/api/v1/projects/{pid}/facts")).json()["total"] == 1
