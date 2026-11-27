import logging
import time
from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware

# Configure a structured logger
logger = logging.getLogger("taskvault.access")
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)-7s | %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)


class LoggingMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        # 1. Start timer
        start_time = time.perf_counter()

        # 2. Process request through FastAPI router
        response = await call_next(request)

        # 3. Calculate processing time in milliseconds
        process_time_ms = (time.perf_counter() - start_time) * 1000

        # 4. Log HTTP method, URL path, status code, and execution time
        logger.info(
            f"{request.method} {request.url.path} - "
            f"Status: {response.status_code} - "
            f"Duration: {process_time_ms:.2f}ms"
        )

        return response