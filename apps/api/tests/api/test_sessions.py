from __future__ import annotations

from pathlib import Path

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient

from main import app

FIXTURES_DIR = Path(__file__).parents[1] / "fixtures"
TINY_CSV = FIXTURES_DIR / "tiny.csv"

SAMPLES_DIR = Path(__file__).parents[4] / "samples"
CHURN_CSV = SAMPLES_DIR / "churn_sample.csv"


@pytest_asyncio.fixture
async def client() -> AsyncClient:
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        yield ac


@pytest.mark.asyncio
async def test_create_session_csv(client: AsyncClient) -> None:
    with open(TINY_CSV, "rb") as f:
        response = await client.post(
            "/sessions",
            files={"file": ("tiny.csv", f, "text/csv")},
        )
    assert response.status_code == 201
    body = response.json()
    assert "id" in body
    assert body["profile"]["facts"]["row_count"] == 3


@pytest.mark.asyncio
async def test_create_session_sample(client: AsyncClient) -> None:
    response = await client.post(
        "/sessions",
        data={"sample_name": "churn_sample"},
    )
    assert response.status_code == 201
    body = response.json()
    assert "id" in body
    assert body["profile"]["facts"]["row_count"] == 20


@pytest.mark.asyncio
async def test_file_too_large(client: AsyncClient) -> None:
    big_content = b"a,b\n" + b"1,2\n" * (11 * 1024 * 1024 // 4)
    response = await client.post(
        "/sessions",
        files={"file": ("big.csv", big_content, "text/csv")},
    )
    assert response.status_code == 413
    assert response.json()["detail"]["error"]["code"] == "file_too_large"


@pytest.mark.asyncio
async def test_bad_extension(client: AsyncClient) -> None:
    response = await client.post(
        "/sessions",
        files={"file": ("data.txt", b"hello world", "text/plain")},
    )
    assert response.status_code == 422
    assert response.json()["detail"]["error"]["code"] == "invalid_file_type"


@pytest.mark.asyncio
async def test_get_session(client: AsyncClient) -> None:
    with open(TINY_CSV, "rb") as f:
        create_resp = await client.post(
            "/sessions",
            files={"file": ("tiny.csv", f, "text/csv")},
        )
    session_id = create_resp.json()["id"]

    response = await client.get(f"/sessions/{session_id}")
    assert response.status_code == 200
    assert response.json()["id"] == session_id


@pytest.mark.asyncio
async def test_get_session_not_found(client: AsyncClient) -> None:
    response = await client.get("/sessions/00000000-0000-0000-0000-000000000000")
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_list_samples(client: AsyncClient) -> None:
    response = await client.get("/samples")
    assert response.status_code == 200
    body = response.json()
    assert len(body["samples"]) >= 1
