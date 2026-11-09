"""Translate domain errors into HTTP responses."""

from __future__ import annotations

from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import exception_handler as drf_exception_handler

from cardcraft.domain.exceptions import NotFoundError, ValidationError


def api_exception_handler(exc, context):
    if isinstance(exc, ValidationError):
        return Response(exc.errors, status=status.HTTP_400_BAD_REQUEST)
    if isinstance(exc, NotFoundError):
        return Response({"detail": str(exc)}, status=status.HTTP_404_NOT_FOUND)
    return drf_exception_handler(exc, context)
