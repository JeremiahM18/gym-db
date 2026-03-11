import time
import uuid
import logging
from fastapi import Request

logger = logging.getLogger("gymdb")

async def request_logging_middleware(request: Request, call_next):
    request_id = request.headers.get("x-request-id") or str(uuid.uuid4())
    start = time.perf_counter()

    response = None
    try:
        response = await call_next(request)
        response.headers["x-request-id"] = request_id
        return response
    except Exception:
        logger.exception(
            "request_error",
            extra={
                "request_id": request_id,
                "method": request.method,
                "path": request.url.path,
                "query": str(request.url.query),
            },
        )
        raise
    finally:
        elapsed_ms = (time.perf_counter() - start) * 1000.0
        status = response.status_code if response else 500

        logger.info(
            "request",
            extra={
                "request_id": request_id,
                "method": request.method,
                "path": request.url.path,
                "query": str(request.url.query),
                "status": status,
                "elapsed_ms": round(elapsed_ms, 2)
            },
        )

