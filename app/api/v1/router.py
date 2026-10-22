from fastapi import APIRouter

from app.api.v1 import contracts, store, users, webhooks

api_router = APIRouter()
api_router.include_router(contracts.router, tags=["contracts"])
api_router.include_router(store.router, tags=["store"])
api_router.include_router(webhooks.router, tags=["payments"])
api_router.include_router(users.router, tags=["users"])
