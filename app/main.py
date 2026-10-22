from fastapi import FastAPI

from app.api.v1.router import api_router

app = FastAPI(
    title="Luweero Build API",
    version="1.0.0",
    summary="Milestone escrow and hardware-store backend",
)
app.include_router(api_router, prefix="/api/v1")


@app.get("/health", tags=["health"])
def health() -> dict[str, str]:
    return {"status": "ok"}
