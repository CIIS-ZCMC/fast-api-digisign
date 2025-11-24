from fastapi import FastAPI
from app.api.endpoints import router as api_router

print("Starting ASGI application...")

app = FastAPI(
    title="Digital Signature API (router only)",
    description="ASGI app that mounts the newest API router from app.api.endpoints",
    version="1.0.0",
)

# Mount the API router from app.api.endpoints
app.include_router(api_router)

# Optional: health check
@app.get("/healthz")
async def healthz():
    return {"status": "ok"}
