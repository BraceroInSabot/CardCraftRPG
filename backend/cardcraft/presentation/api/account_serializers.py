"""Payloads of the authentication and settings endpoints."""

from __future__ import annotations

from rest_framework import serializers

from cardcraft.domain.accounts import DISPLAY_NAME_MAX_LENGTH, EMAIL_MAX_LENGTH


class LoginSerializer(serializers.Serializer):
    username = serializers.CharField(max_length=150, trim_whitespace=True)
    password = serializers.CharField(max_length=128, trim_whitespace=False)


class MasterSerializer(serializers.Serializer):
    id = serializers.IntegerField(read_only=True)
    username = serializers.CharField(read_only=True)
    display_name = serializers.CharField(read_only=True)
    email = serializers.CharField(read_only=True)
    default_background_color = serializers.CharField(read_only=True)


class ProfileSerializer(serializers.Serializer):
    display_name = serializers.CharField(max_length=DISPLAY_NAME_MAX_LENGTH, required=False, allow_blank=True)
    email = serializers.EmailField(max_length=EMAIL_MAX_LENGTH, required=False, allow_blank=True)


class CardDefaultsSerializer(serializers.Serializer):
    default_background_color = serializers.RegexField(
        r"^#[0-9a-fA-F]{6}$",
        error_messages={"invalid": "Use a hex color such as #ffffff."},
    )


class PasswordChangeSerializer(serializers.Serializer):
    current_password = serializers.CharField(max_length=128, trim_whitespace=False)
    new_password = serializers.CharField(max_length=128, trim_whitespace=False)
