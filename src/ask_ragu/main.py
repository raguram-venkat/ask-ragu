from fastapi import FastAPI

from ask_ragu.api import chat, health, webhook

app = FastAPI(title="ask-ragu")
app.include_router(health.router)
app.include_router(webhook.router)
app.include_router(chat.router)
