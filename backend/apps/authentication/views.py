from __future__ import annotations

import logging
from django.conf import settings
from django.contrib.auth import get_user_model
from rest_framework import permissions, status
from rest_framework.authtoken.models import Token
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.authentication.models import UserProfile
from apps.authentication.serializers import (
    GitHubAuthSerializer,
    GoogleAuthSerializer,
    LoginSerializer,
    SignupSerializer,
    UserSerializer,
)
from apps.authentication.services.oauth import exchange_github_oauth, exchange_google_oauth

logger = logging.getLogger(__name__)
User = get_user_model()


class MeView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        serializer = UserSerializer(request.user)
        return Response({"user": serializer.data})


class LoginView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        serializer = LoginSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.validated_data["user"]
        token, _ = Token.objects.get_or_create(user=user)
        return Response(
            {
                "user": UserSerializer(user).data,
                "token": token.key,
            },
            status=status.HTTP_200_OK,
        )


class SignupView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        serializer = SignupSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        token, _ = Token.objects.get_or_create(user=user)
        return Response(
            {
                "user": UserSerializer(user).data,
                "token": token.key,
            },
            status=status.HTTP_201_CREATED,
        )


class GitHubAuthView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        serializer = GitHubAuthSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        try:
            user, token_key, created = exchange_github_oauth(
                code=data["code"],
                redirect_uri=data.get("redirect_uri") or None,
            )
            return Response(
                {
                    "user": UserSerializer(user).data,
                    "token": token_key,
                    "created": created,
                },
                status=status.HTTP_200_OK,
            )
        except ValueError as exc:
            return Response({"detail": str(exc)}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as exc:
            logger.exception("GitHub auth failed: %s", exc)
            return Response(
                {"detail": f"GitHub login failed: {exc}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )


class GoogleAuthView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        serializer = GoogleAuthSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        try:
            user, token_key, created = exchange_google_oauth(
                code=data.get("code") or None,
                id_token_str=data.get("id_token") or None,
                redirect_uri=data.get("redirect_uri") or None,
            )
            return Response(
                {
                    "user": UserSerializer(user).data,
                    "token": token_key,
                    "created": created,
                },
                status=status.HTTP_200_OK,
            )
        except ValueError as exc:
            return Response({"detail": str(exc)}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as exc:
            logger.exception("Google auth failed: %s", exc)
            return Response(
                {"detail": f"Google login failed: {exc}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )


class LogoutView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        Token.objects.filter(user=request.user).delete()
        return Response({"detail": "Successfully logged out."}, status=status.HTTP_200_OK)


class DemoLoginView(APIView):
    """Allows zero-friction demo exploration without configuring external OAuth keys."""
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        user, _ = User.objects.get_or_create(
            username="demo_user",
            defaults={"email": "demo@codescope.io", "first_name": "Demo", "last_name": "User"},
        )
        UserProfile.objects.get_or_create(
            user=user,
            defaults={"avatar_url": "https://api.dicebear.com/7.x/bottts/svg?seed=demo", "provider": "email"},
        )
        token, _ = Token.objects.get_or_create(user=user)
        return Response(
            {
                "user": UserSerializer(user).data,
                "token": token.key,
            },
            status=status.HTTP_200_OK,
        )


class ProvidersConfigView(APIView):
    """Exposes which OAuth providers are configured with client IDs."""
    permission_classes = [permissions.AllowAny]

    def get(self, request):
        gh_client_id = getattr(settings, "GITHUB_CLIENT_ID", "")
        google_client_id = getattr(settings, "GOOGLE_CLIENT_ID", "")
        return Response(
            {
                "github": {
                    "enabled": bool(gh_client_id),
                    "client_id": gh_client_id,
                },
                "google": {
                    "enabled": bool(google_client_id),
                    "client_id": google_client_id,
                },
            }
        )
