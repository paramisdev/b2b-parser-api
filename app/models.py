from pydantic import BaseModel, HttpUrl


class ParseRequest(BaseModel):
    url: HttpUrl


class CarListing(BaseModel):
    title: str
    price: int
    currency: str
    mileage: int | None = None
    year: int | None = None
    url: HttpUrl
