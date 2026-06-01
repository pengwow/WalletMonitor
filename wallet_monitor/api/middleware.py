"""
API middleware for WalletMonitor.

Provides:
  - PaginatedResponse model + paginate() helper for consistent list endpoints
  - Global exception handler (catches unhandled errors → JSON)
  - Request-ID middleware (generates a UUID per request, injects into logs)
  - API-key authentication middleware (reads SECRET_KEY from config)

Usage in app.py:
    from .api.middleware import (
        register_middleware,
        PaginatedResponse,
        paginate,
        get_current_user,
    )
"""

from __future__ import annotations

import logging
import time
import uuid
from typing import Any, Callable, Dict, Generic, List, Optional, Sequence, TypeVar

from fastapi import FastAPI, HTTPException, Request, Response, Depends
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field

from ..logging_config import _RequestIdFilter, request_id_context
from ..config import settings

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# 1. Pagination helpers
# ---------------------------------------------------------------------------

T = TypeVar("T")


class PaginatedResponse(BaseModel, Generic[T]):
    """Standard paginated envelope returned by list endpoints."""

    items: List[T] = Field(..., description="Page of results")
    total: int = Field(..., description="Total number of matching records")
    page: int = Field(..., description="Current page number (1-based)")
    page_size: int = Field(..., description="Items per page")
    total_pages: int = Field(..., description="Total number of pages")


def paginate(
    items: Sequence[Any],
    total: int,
    page: int,
    page_size: int,
) -> Dict[str, Any]:
    """Build a ``PaginatedResponse``-compatible dict from raw data.

    Parameters
    ----------
    items:
        The slice of results for the current page.
    total:
        Total count of all matching records (before slicing).
    page:
        Current 1-based page number.
    page_size:
        Number of items per page.
    """
    total_pages = max(1, (total + page_size - 1) // page_size)
    return {
        "items": list(items),
        "total": total,
        "page": page,
        "page_size": page_size,
        "total_pages": total_pages,
    }


# ---------------------------------------------------------------------------
# 2. Global exception handler
# ---------------------------------------------------------------------------

async def global_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """Catch-all handler for unhandled exceptions.

    Returns a consistent JSON shape so clients never see raw tracebacks.
    """
    request_id = getattr(request.state, "request_id", "-")

    # Log the full traceback at ERROR level for debugging
    logger.error(
        "Unhandled exception [req:%s] %s %s → %s",
        request_id,
        request.method,
        request.url.path,
        exc,
        exc_info=True,
    )

    # Don't leak internal details in production
    if isinstance(exc, HTTPException):
        return JSONResponse(
            status_code=exc.status_code,
            content={
                "error": True,
                "detail": exc.detail,
                "request_id": request_id,
            },
        )

    return JSONResponse(
        status_code=500,
        content={
            "error": True,
            "detail": "Internal server error",
            "request_id": request_id,
        },
    )


# ---------------------------------------------------------------------------
# 3. Request-ID middleware
# ---------------------------------------------------------------------------

async def request_id_middleware(request: Request, call_next: Callable) -> Response:
    """Assign a unique request ID to every incoming request.

    The ID is:
      - Read from the ``X-Request-ID`` header if present, otherwise generated.
      - Attached to ``request.state.request_id`` for downstream handlers.
      - Injected into the logging context via ``_RequestIdFilter``.
      - Returned in the ``X-Request-ID`` response header.
    """
    rid = request.headers.get("X-Request-ID") or str(uuid.uuid4())
    request.state.request_id = rid

    # Inject into the logging filter so all log records carry this ID
    _RequestIdFilter.set_request_id(rid)

    start = time.monotonic()
    response: Response = await call_next(request)
    elapsed_ms = round((time.monotonic() - start) * 1000, 1)

    response.headers["X-Request-ID"] = rid
    response.headers["X-Response-Time"] = f"{elapsed_ms}ms"

    logger.info(
        "%s %s → %s (%sms)",
        request.method,
        request.url.path,
        response.status_code,
        elapsed_ms,
    )

    # Clean up so the ID doesn't leak into unrelated async tasks
    _RequestIdFilter.set_request_id("-")

    return response


# ---------------------------------------------------------------------------
# 4. API-key authentication
# ---------------------------------------------------------------------------

def _get_api_key(request: Request) -> Optional[str]:
    """Extract the API key from the ``Authorization`` header.

    Accepted formats:
      - ``Authorization: Bearer <key>``
      - ``Authorization: <key>``
      - ``X-API-Key: <key>``
    """
    # Check X-API-Key first (simpler for non-browser clients)
    api_key = request.headers.get("X-API-Key")
    if api_key:
        return api_key

    auth_header = request.headers.get("Authorization", "")
    if auth_header.startswith("Bearer "):
        return auth_header[7:].strip()
    if auth_header:
        return auth_header.strip()

    return None


async def verify_api_key(request: Request) -> Dict[str, Any]:
    """FastAPI dependency that validates the API key.

    If the configured ``secret_key`` is the default placeholder, auth is
    **bypassed** so local development works out of the box.

    Returns a dict with the verified key info on success, raises 401 on
    failure.
    """
    configured_key = settings.secret_key

    # Skip auth when using the default placeholder key
    if configured_key == "change-me-in-production":
        return {"authenticated": False, "reason": "auth-disabled-default-key"}

    provided_key = _get_api_key(request)

    if not provided_key:
        raise HTTPException(
            status_code=401,
            detail="Missing API key. Provide via 'Authorization: Bearer <key>' or 'X-API-Key' header.",
        )

    if provided_key != configured_key:
        logger.warning(
            "Authentication failed from %s",
            request.client.host if request.client else "unknown",
        )
        raise HTTPException(status_code=401, detail="Invalid API key")

    return {"authenticated": True}


# Shorthand dependency alias so routers can write: Depends(require_auth)
require_auth = Depends(verify_api_key)


# ---------------------------------------------------------------------------
# 5. Setup helper – register everything on the FastAPI app
# ---------------------------------------------------------------------------

def register_middleware(app: FastAPI) -> None:
    """Register all middleware and exception handlers on *app*.

    Call this once in ``create_app()`` after creating the FastAPI instance.
    """
    # Exception handlers (must be added before middleware)
    app.add_exception_handler(Exception, global_exception_handler)

    # Middleware (executed in reverse order – last added runs first)
    app.middleware("http")(request_id_middleware)

    logger.info("API middleware registered (request-id, global-error-handler)")
