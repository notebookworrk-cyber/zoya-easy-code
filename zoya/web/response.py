"""Zoya 4.0 Response module.

Provides standardized API response format with success, data, error, and meta fields.
"""

from typing import Any, Dict, Optional, TypedDict


class ResponseData(TypedDict):
    """Standardized API response format with success, data, error, and meta fields."""
    success: bool
    data: Optional[Any]
    error: Optional[str]
    meta: Optional[Dict[str, Any]]


# Status code constants
HTTP_200_OK = 200
HTTP_400_BAD_REQUEST = 400
HTTP_401_UNAUTHORIZED = 401
HTTP_403_FORBIDDEN = 403
HTTP_404_NOT_FOUND = 404
HTTP_500_INTERNAL_SERVER_ERROR = 500


def create_success(
    data: Any,
    meta: Optional[Dict[str, Any]] = None,
    status: int = HTTP_200_OK,
) -> ResponseData:
    """Create a successful API response.

    Args:
        data: Payload to return.
        meta: Optional metadata (e.g., pagination).
        status: HTTP status code (default 200).

    Returns:
        ResponseData dict.
    """
    return {
        "success": True,
        "data": data,
        "error": None,
        "meta": meta,
    }


def create_error(
    message: str,
    status: int = HTTP_400_BAD_REQUEST,
    meta: Optional[Dict[str, Any]] = None,
) -> ResponseData:
    """Create an error API response.

    Args:
        message: Error message description.
        status: HTTP status code (default 400).
        meta: Optional metadata.

    Returns:
        ResponseData dict.
    """
    return {
        "success": False,
        "data": None,
        "error": message,
        "meta": meta,
    }
