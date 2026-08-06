"""RFC 7807-style API exception handler."""

from __future__ import annotations

from typing import Any

from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import exception_handler


def codescope_exception_handler(exc: Exception, context: dict[str, Any]) -> Response | None:
    response = exception_handler(exc, context)
    if response is None:
        return None

    request = context.get("request")
    instance = request.path if request is not None else None
    title = response.status_text or "Error"
    detail = response.data

    if isinstance(detail, dict) and "detail" in detail and len(detail) == 1:
        detail_value = detail["detail"]
    else:
        detail_value = detail

    response.data = {
        "type": "about:blank",
        "title": title,
        "status": response.status_code,
        "detail": detail_value,
        "instance": instance,
    }
    return response


class ServiceUnavailable(Exception):
    """Raised when a dependency (Neo4j, Redis) is down."""

    status_code = status.HTTP_503_SERVICE_UNAVAILABLE
