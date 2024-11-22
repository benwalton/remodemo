from contextlib import asynccontextmanager

import uvicorn
from fastapi import FastAPI

from db import ensure_indexes
from routers.transaction_router import TransactionRouter


def remodemo_app():
    app = FastAPI()

    transaction_router = TransactionRouter()

    app.include_router(transaction_router.router)

    return app


app = remodemo_app()


@asynccontextmanager
async def lifespan():
    await ensure_indexes()


if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, log_level="info", reload=True)
