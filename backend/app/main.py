from fastapi import FastAPI

from app.api.routes import router
from app.core.config import get_settings


settings = get_settings()
app = FastAPI(title=settings.app_name)
app.include_router(router)


@app.get("/api/health")
def health() -> dict[str, str]:
    return {"status": "ok", "app": settings.app_name}
