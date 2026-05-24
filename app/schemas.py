from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class ItemCreate(BaseModel):
    """Payload for POST /items."""

    name: str = Field(..., max_length=255, examples=["Widget"])
    description: str | None = Field(None, max_length=1024)
    price: float = Field(..., ge=0, examples=[9.99])


class ItemRead(BaseModel):
    """Item as returned by the API."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    description: str | None
    price: float
    created_at: datetime
