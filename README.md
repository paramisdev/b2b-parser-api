# B2B Parser API

HTTP-сервис для получения нормализованных данных об автомобиле по ссылке на
объявление. Сервис принимает URL, обращается к внешнему API провайдера и
возвращает карточку автомобиля в едином формате.

## Стек

- Python 3.12
- FastAPI
- httpx
- Pydantic v2
- pydantic-settings
- uv
- Docker
- pytest, ruff, mypy

## Возможности

- `POST /parse` с валидацией входного URL;
- асинхронный запрос к provider API через `httpx.AsyncClient`;
- проверка ответа через Pydantic-модели;
- обработка ошибок провайдера:
  - `404` — объявление не найдено;
  - `504` — таймаут провайдера;
  - `502` — некорректный ответ или ошибка внешнего API;
- секреты хранятся через `SecretStr` и `.env`.

## Быстрый старт

Требования: Python 3.12+ и [uv](https://docs.astral.sh/uv/).

```bash
uv sync --locked
cp .env.example .env
```

Заполните `.env`:

```dotenv
PROVIDER_API_KEY=your-provider-api-key
PROVIDER_BASE_URL=https://api.provider.example
PROVIDER_TIMEOUT_SECONDS=10
```

Запуск приложения:

```bash
uv run uvicorn app.main:app --reload
```

API будет доступно по адресу `http://127.0.0.1:8000`.
Документация FastAPI: `http://127.0.0.1:8000/docs`.

## Пример запроса

```bash
curl -X POST http://127.0.0.1:8000/parse \
  -H "Content-Type: application/json" \
  -d '{"url":"https://www.avito.ru/moskva/avtomobili/toyota_camry_123"}'
```

Пример ответа:

```json
{
  "title": "Toyota Camry 2.5",
  "price": 1500000,
  "currency": "RUB",
  "mileage": 45000,
  "year": 2020,
  "url": "https://www.avito.ru/moskva/avtomobili/toyota_camry_123"
}
```

## Переменные окружения

| Переменная | Обязательна | Описание |
|---|---|---|
| `PROVIDER_API_KEY` | да | API-ключ провайдера |
| `PROVIDER_BASE_URL` | да | Базовый URL API провайдера |
| `PROVIDER_TIMEOUT_SECONDS` | нет | Таймаут запроса, по умолчанию `10` |

## Тесты и проверки

```bash
uv run pytest -q
uv run ruff check .
uv run ruff format --check .
uv run mypy app
```

## Docker

```bash
docker build -t b2b-parser-api .
docker run --rm -p 8000:8000 --env-file .env b2b-parser-api
```

## Структура проекта

```text
app/
  main.py          # FastAPI-приложение и POST /parse
  config.py        # настройки через pydantic-settings
  models.py        # ParseRequest и CarListing
  services/
    provider.py    # клиент внешнего provider API
tests/
  test_parse.py    # контрактные тесты эндпоинта
```
