import httpx
from pydantic import ValidationError

from app.models import CarListing


class ProviderError(Exception): ...


class ProviderNotFoundError(ProviderError): ...


class ProviderTimeoutError(ProviderError): ...


class ProviderResponseError(ProviderError): ...


async def fetch_car_listing(client: httpx.AsyncClient, url: str) -> CarListing:
    try:
        response = await client.get("/parse", params={"url": url})

        response.raise_for_status()

        data = response.json()

        return CarListing.model_validate(data)

    except httpx.TimeoutException as exc:
        raise ProviderTimeoutError("Превышено время ожидания от провайдера") from exc

    except httpx.HTTPStatusError as exc:
        if exc.response.status_code == 404:
            raise ProviderNotFoundError("Объявление не найдено") from exc
        raise ProviderResponseError(
            f"Ошибка API провайдера: статус {exc.response.status_code}"
        ) from exc

    except httpx.HTTPError as exc:
        raise ProviderResponseError("Сетевая ошибка при запросе к API") from exc

    except (ValueError, ValidationError) as exc:
        raise ProviderResponseError("Некорректный формат данных от провайдера") from exc
