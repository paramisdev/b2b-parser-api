from collections.abc import AsyncGenerator
from typing import Annotated

import httpx
from fastapi import Depends, FastAPI, HTTPException

from app.config import get_settings
from app.models import CarListing, ParseRequest
from app.services.provider import (
    ProviderNotFoundError,
    ProviderResponseError,
    ProviderTimeoutError,
    fetch_car_listing,
)

app = FastAPI(title="B2B Parser")


async def get_http_client() -> AsyncGenerator[httpx.AsyncClient, None]:
    settings = get_settings()
    headers = {"Authorization": f"Bearer {settings.provider_api_key.get_secret_value()}"}
    async with httpx.AsyncClient(
        base_url=str(settings.provider_base_url),
        timeout=settings.provider_timeout_seconds,
        headers=headers,
    ) as client:
        yield client


@app.post("/parse", response_model=CarListing)
async def parse_listing(
    payload: ParseRequest,
    client: Annotated[httpx.AsyncClient, Depends(get_http_client)],
) -> CarListing:
    try:
        return await fetch_car_listing(client, str(payload.url))
    except ProviderNotFoundError as exc:
        raise HTTPException(status_code=404, detail="Listing not found") from exc
    except ProviderTimeoutError as exc:
        raise HTTPException(status_code=504, detail="Provider timeout") from exc
    except ProviderResponseError as exc:
        raise HTTPException(status_code=502, detail="Provider error") from exc
