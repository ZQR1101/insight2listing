"""End-to-end creative API tests (Phase E)."""

from __future__ import annotations

import csv
import io

import httpx
import pytest_asyncio
from PIL import Image  # type: ignore[import-untyped]

from conftest import create_project


def _png(width: int = 1000, height: int = 1000, color=(210, 210, 210)) -> bytes:
    image = Image.new("RGB", (width, height), color)
    buffer = io.BytesIO()
    image.save(buffer, format="PNG")
    return buffer.getvalue()


def _products_csv(rows: list[dict]) -> bytes:
    buf = io.StringIO()
    w = csv.DictWriter(buf, fieldnames=["external_id", "title", "brand"])
    w.writeheader()
    w.writerows(rows)
    return buf.getvalue().encode("utf-8")


async def _upload(
    client: httpx.AsyncClient,
    pid: str,
    product_id: str,
    data: bytes,
    *,
    attested: bool = True,
    content_type: str = "image/png",
):
    return await client.post(
        f"/api/v1/projects/{pid}/products/{product_id}/images",
        files={"file": ("photo.png", data, content_type)},
        data={"rights_attested": "true" if attested else "false"},
    )


@pytest_asyncio.fixture
async def project_with_product(client: httpx.AsyncClient) -> dict:
    project = await create_project(client, name="Creative Project")
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


async def test_upload_requires_rights_attestation(client, project_with_product) -> None:
    pid = project_with_product["project"]["id"]
    product_id = project_with_product["product"]["id"]
    resp = await _upload(client, pid, product_id, _png(), attested=False)
    assert resp.status_code == 422
    assert "rights" in resp.json()["detail"]


async def test_upload_rejects_small_images(client, project_with_product) -> None:
    pid = project_with_product["project"]["id"]
    product_id = project_with_product["product"]["id"]
    resp = await _upload(client, pid, product_id, _png(500, 500))
    assert resp.status_code == 422
    assert "1000" in resp.json()["detail"]


async def test_upload_rejects_non_images(client, project_with_product) -> None:
    pid = project_with_product["project"]["id"]
    product_id = project_with_product["product"]["id"]
    resp = await client.post(
        f"/api/v1/projects/{pid}/products/{product_id}/images",
        files={"file": ("notes.txt", b"just text", "text/plain")},
        data={"rights_attested": "true"},
    )
    assert resp.status_code == 422


async def test_upload_dedup_and_file_preview(client, project_with_product) -> None:
    pid = project_with_product["project"]["id"]
    product_id = project_with_product["product"]["id"]
    payload = _png()

    first = await _upload(client, pid, product_id, payload)
    assert first.status_code == 201, first.text

    duplicate = await _upload(client, pid, product_id, payload)
    assert duplicate.status_code == 409
    assert duplicate.json()["detail"]["existing_id"] == first.json()["id"]

    listed = (await client.get(f"/api/v1/projects/{pid}/products/{product_id}/images")).json()
    assert listed["total"] == 1

    file = await client.get(f"/api/v1/projects/{pid}/images/{first.json()['id']}/file")
    assert file.status_code == 200
    assert file.content == payload


async def test_main_image_edit_requires_source(client, project_with_product) -> None:
    pid = project_with_product["project"]["id"]
    product_id = project_with_product["product"]["id"]
    resp = await client.post(
        f"/api/v1/projects/{pid}/products/{product_id}/creatives/generate",
        json={"asset_type": "main_image_edit"},
    )
    assert resp.status_code == 422
    assert "source photo" in resp.json()["detail"]


async def test_main_image_edit_forbids_overlay(client, project_with_product) -> None:
    pid = project_with_product["project"]["id"]
    product_id = project_with_product["product"]["id"]
    image_id = (await _upload(client, pid, product_id, _png())).json()["id"]

    resp = await client.post(
        f"/api/v1/projects/{pid}/products/{product_id}/creatives/generate",
        json={"asset_type": "main_image_edit", "source_image_ids": [image_id], "overlay_lines": ["200 ml"]},
    )
    assert resp.status_code == 422
    assert "must not contain added text" in resp.json()["detail"]


async def test_main_image_pipeline_and_approval_gate(client, project_with_product) -> None:
    pid = project_with_product["project"]["id"]
    product_id = project_with_product["product"]["id"]
    image_id = (await _upload(client, pid, product_id, _png())).json()["id"]

    created = await client.post(
        f"/api/v1/projects/{pid}/products/{product_id}/creatives/generate",
        json={"asset_type": "main_image_edit", "source_image_ids": [image_id]},
    )
    assert created.status_code == 201, created.text
    creative = created.json()
    assert creative["consistency_status"] == "passed"
    assert creative["compliance_status"] == "passed"
    assert creative["human_review_status"] == "pending"
    assert creative["source_images"] == [image_id]

    creative_id = creative["id"]
    preview = await client.get(f"/api/v1/projects/{pid}/creatives/{creative_id}/file")
    assert preview.status_code == 200  # preview allowed before approval

    denied = await client.get(f"/api/v1/projects/{pid}/creatives/{creative_id}/download")
    assert denied.status_code == 403  # export gate: approval required

    approved = await client.post(f"/api/v1/projects/{pid}/creatives/{creative_id}/approve")
    assert approved.status_code == 200
    assert approved.json()["human_review_status"] == "approved"

    download = await client.get(f"/api/v1/projects/{pid}/creatives/{creative_id}/download")
    assert download.status_code == 200
    assert download.content == (await client.get(
        f"/api/v1/projects/{pid}/images/{image_id}/file"
    )).content  # mock edit preserves the real product photo

    project = (await client.get(f"/api/v1/projects/{pid}")).json()
    assert project["status"] == "CREATIVES_GENERATED"


async def test_lifestyle_generation_with_overlay(client, project_with_product) -> None:
    pid = project_with_product["project"]["id"]
    product_id = project_with_product["product"]["id"]
    resp = await client.post(
        f"/api/v1/projects/{pid}/products/{product_id}/creatives/generate",
        json={
            "asset_type": "lifestyle_image",
            "overlay_lines": ["200 ml"],
        },
    )
    assert resp.status_code == 201, resp.text
    creative = resp.json()
    assert creative["width"] == 1024
    assert creative["consistency_status"] == "passed"
    assert creative["compliance_status"] == "passed"

    preview = await client.get(f"/api/v1/projects/{pid}/creatives/{creative['id']}/file")
    assert preview.status_code == 200
    with Image.open(io.BytesIO(preview.content)) as image:
        assert image.size == (1024, 1024)

    reject = await client.post(f"/api/v1/projects/{pid}/creatives/{creative['id']}/reject")
    assert reject.status_code == 200
    assert reject.json()["human_review_status"] == "rejected"
