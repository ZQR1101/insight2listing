"""Workspace and project lifecycle tests."""

from __future__ import annotations

from httpx import AsyncClient

from conftest import create_project


async def test_default_workspace(client: AsyncClient) -> None:
    resp = await client.get("/api/v1/workspaces")
    assert resp.status_code == 200, resp.text
    assert resp.json()["name"]


async def test_create_and_get_project(client: AsyncClient) -> None:
    created = await create_project(client, name="Packing Cubes")
    assert created["status"] == "DRAFT"
    assert created["name"] == "Packing Cubes"

    got = await client.get(f"/api/v1/projects/{created['id']}")
    assert got.status_code == 200
    assert got.json()["id"] == created["id"]


async def test_list_projects(client: AsyncClient) -> None:
    await create_project(client, name="A")
    await create_project(client, name="B")
    resp = await client.get("/api/v1/projects")
    assert resp.status_code == 200
    assert resp.json()["total"] == 2
    assert len(resp.json()["items"]) == 2


async def test_project_status_transition(client: AsyncClient) -> None:
    project = await create_project(client)
    resp = await client.patch(
        f"/api/v1/projects/{project['id']}/status", json={"status": "DATA_IMPORTED"}
    )
    assert resp.status_code == 200
    assert resp.json()["status"] == "DATA_IMPORTED"


async def test_get_missing_project_404(client: AsyncClient) -> None:
    resp = await client.get("/api/v1/projects/11111111-1111-1111-1111-111111111111")
    assert resp.status_code == 404
