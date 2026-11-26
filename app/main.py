from fastapi import FastAPI

from app.core.config import settings
from app.routers import auth, tasks

app = FastAPI(
    title=settings.PROJECT_NAME,
    version="1.0.0",
    description="TaskVault REST API",
)

# Register routers
app.include_router(auth.router)
app.include_router(tasks.router)


@app.get("/health", tags=["Health"])
def health_check():
    return {"status": "healthy"}
