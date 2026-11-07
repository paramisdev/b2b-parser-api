from collections.abc import AsyncIterator, Callable
from contextlib import asynccontextmanager

import httpx
import pytest

from app.main import app, get_http_client

PROVIDER_BASE_URL = "https://provider.test"
LISTING_URL = "https://www.avito.ru/moskva/avtomobili/toyota_camry_123"
PROVIDER_API_KEY = "test-provider-key"

CAR_PAYLOAD = {
    "title": "Toyota Camry 2.5",
    "price": 1_500_000,
    "currency": "RUB",
    "mileage": 45_000,
    "year": 2020,
    "url": LISTING_URL,
}

Handler = Callable[[httpx.Request], httpx.Response]


@asynccontextmanager
async def make_client(handler: Handler) -> AsyncIterator[httpx.AsyncClient]:
    transport = httpx.MockTransport(handler)

    async def override_http_client() -> AsyncIterator[httpx.AsyncClient]:
        async with httpx.AsyncClient(
            transport=transport,
            base_url=PROVIDER_BASE_URL,
            headers={"Authorization": f"Bearer {PROVIDER_API_KEY}"},
        ) as client:
            yield client

    app.dependency_overrides[get_http_client] = override_http_client
    try:
        async with httpx.AsyncClient(
            transport=httpx.ASGITransport(app=app),
            base_url="http://testserver",
        ) as client:
            yield client
    finally:
        app.dependency_overrides.clear()


async def test_parse_returns_car_listing() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        assert request.method == "GET"
        assert request.url.path == "/parse"
        assert request.url.params["url"] == LISTING_URL
        assert request.headers["Authorization"] == f"Bearer {PROVIDER_API_KEY}"
        return httpx.Response(200, json=CAR_PAYLOAD, request=request)

    async with make_client(handler) as client:
        response = await client.post("/parse", json={"url": LISTING_URL})

    assert response.status_code == 200
    assert response.json() == CAR_PAYLOAD


async def test_provider_404_is_returned_to_client() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(404, json={"detail": "listing not found"}, request=request)

    async with make_client(handler) as client:
        response = await client.post("/parse", json={"url": LISTING_URL})

    assert response.status_code == 404


async def test_provider_timeout_returns_gateway_timeout() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        raise httpx.ReadTimeout("provider timed out", request=request)

    async with make_client(handler) as client:
        response = await client.post("/parse", json={"url": LISTING_URL})

    assert response.status_code == 504


async def test_invalid_url_is_rejected_before_provider_call() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        pytest.fail("provider must not be called for invalid input")

    async with make_client(handler) as client:
        response = await client.post("/parse", json={"url": "not-a-valid-url"})

    assert response.status_code == 422
