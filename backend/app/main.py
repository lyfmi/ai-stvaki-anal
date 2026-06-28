from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api import admin, auth, internal, user, webhooks
from app.core.redis import close_redis


@asynccontextmanager
async def lifespan(app: FastAPI):
    yield
    await close_redis()


app = FastAPI(title="AI Bet Bot API", version="1.0.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(user.router)
app.include_router(admin.router)
app.include_router(internal.router)
app.include_router(webhooks.router)
app.include_router(webhooks.payments_router)


@app.get("/health")
async def health():
    return {"status": "ok"}
