from contextlib import asynccontextmanager

from fastapi import Depends, FastAPI, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app import crud
from app.database import engine, get_session
from app.schemas import ItemCreate, ItemRead


@asynccontextmanager
async def lifespan(app: FastAPI):
    yield
    # Dispose pooled connections on shutdown so uvicorn exits cleanly.
    await engine.dispose()


app = FastAPI(
    title="FastAPI Template",
    description="Starter backend: FastAPI + SQLAlchemy (async) + Alembic + Pydantic.",
    version="0.1.0",
    lifespan=lifespan,
)


@app.get("/healthz")
async def healthz():
    return {"status": "ok"}


@app.get("/items", response_model=list[ItemRead])
async def list_items(session: AsyncSession = Depends(get_session)):
    return await crud.list_items(session)


@app.get("/items/{item_id}", response_model=ItemRead)
async def get_item(item_id: int, session: AsyncSession = Depends(get_session)):
    item = await crud.get_item(session, item_id)
    if item is None:
        raise HTTPException(status_code=404, detail=f"Item {item_id} not found")
    return item


@app.post("/items", response_model=ItemRead, status_code=201)
async def create_item(payload: ItemCreate, session: AsyncSession = Depends(get_session)):
    return await crud.create_item(session, payload)
