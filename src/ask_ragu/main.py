import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI

from ask_ragu import db
from ask_ragu.api import chat, health, webhook

log = logging.getLogger("uvicorn.error")


@asynccontextmanager
async def lifespan(app: FastAPI):
    with db.connect() as conn:
        log.info("migrations applied: %s", db.migrate(conn) or "none")
    yield


app = FastAPI(title="ask-ragu", lifespan=lifespan)
app.include_router(health.router)
app.include_router(webhook.router)
app.include_router(chat.router)
