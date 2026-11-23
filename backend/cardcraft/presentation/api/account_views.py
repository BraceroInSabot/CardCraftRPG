"""Login, logout and the Master's own settings.

Signing in and out is a transport concern (it creates or ends the Django
session), so it uses ``django.contrib.auth`` directly. Everything about the
account itself goes through the account use cases.
"""

from __future__ import annotations

from django.contrib.auth import authenticate, login, logout, update_session_auth_hash
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_protect, ensure_csrf_cookie
from rest_framework import status
from rest_framework.permissions import AllowAny
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.throttling import ScopedRateThrottle
from rest_framework.views import APIView

from cardcraft.application import AccountUseCases
from cardcraft.container import get_account_use_cases

from .account_serializers import (
    CardDefaultsSerializer,
    LoginSerializer,
    MasterSerializer,
    PasswordChangeSerializer,
    ProfileSerializer,
)

# Same message for unknown users and wrong passwords: never reveal which one failed.
INVALID_CREDENTIALS = "Invalid username or password."


def _accounts() -> AccountUseCases:
    return get_account_use_cases()


def _render(master) -> dict:
    return MasterSerializer(master).data


@method_decorator(ensure_csrf_cookie, name="dispatch")
class CsrfView(APIView):
    """Sets the ``csrftoken`` cookie the SPA must echo on unsafe requests."""

    permission_classes = [AllowAny]

    def get(self, request: Request) -> Response:
        return Response(status=status.HTTP_204_NO_CONTENT)


@method_decorator(csrf_protect, name="dispatch")
class LoginView(APIView):
    permission_classes = [AllowAny]
    throttle_classes = [ScopedRateThrottle]
    throttle_scope = "login"

    def post(self, request: Request) -> Response:
        serializer = LoginSerializer(data=request.data)
        if not serializer.is_valid():
            return Response({"detail": INVALID_CREDENTIALS}, status=status.HTTP_400_BAD_REQUEST)
        user = authenticate(request._request, **serializer.validated_data)
        if user is None:
            return Response({"detail": INVALID_CREDENTIALS}, status=status.HTTP_400_BAD_REQUEST)
        login(request._request, user)  # rotates the session key and the CSRF token
        return Response(_render(_accounts().get.execute(user.pk)))


@method_decorator(csrf_protect, name="dispatch")
class LogoutView(APIView):
    permission_classes = [AllowAny]  # logging out twice is harmless

    def post(self, request: Request) -> Response:
        logout(request._request)
        return Response(status=status.HTTP_204_NO_CONTENT)


class AccountView(APIView):
    """``GET`` the signed-in Master; the SPA also uses it to check the session."""

    def get(self, request: Request) -> Response:
        return Response(_render(_accounts().get.execute(request.user.pk)))


class ProfileView(APIView):
    def patch(self, request: Request) -> Response:
        serializer = ProfileSerializer(data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        master = _accounts().update_profile.execute(request.user.pk, serializer.validated_data)
        return Response(_render(master))


class CardDefaultsView(APIView):
    def patch(self, request: Request) -> Response:
        serializer = CardDefaultsSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        master = _accounts().update_card_defaults.execute(request.user.pk, serializer.validated_data)
        return Response(_render(master))


class PasswordView(APIView):
    def post(self, request: Request) -> Response:
        serializer = PasswordChangeSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        _accounts().change_password.execute(request.user.pk, **serializer.validated_data)
        # Keep this session signed in; every other session of the Master is invalidated.
        request.user.refresh_from_db()
        update_session_auth_hash(request._request, request.user)
        return Response(status=status.HTTP_204_NO_CONTENT)
