import logging
import time
import uuid

from fastapi import Request

from gymdb.observe.metrics import record_http_exception, record_http_request

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
        record_http_exception()
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
        record_http_request(status_code=status, elapsed_ms=elapsed_ms)

        logger.info(
            "request",
            extra={
                "request_id": request_id,
                "method": request.method,
                "path": request.url.path,
                "query": str(request.url.query),
                "status": status,
                "elapsed_ms": round(elapsed_ms, 2),
            },
        )

