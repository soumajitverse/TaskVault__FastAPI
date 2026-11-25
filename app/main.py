from fastapi import FastAPI

from app.core.config import settings

app = FastAPI(
    title=settings.PROJECT_NAME,
    version="1.0.0",
    description="TaskVault REST API",
)


@app.get("/health", tags=["Health"])
def health_check():
    return {"status": "healthy"}
