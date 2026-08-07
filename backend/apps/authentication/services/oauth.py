from __future__ import annotations

import json
import logging
import urllib.parse
import urllib.request
from typing import Any, Tuple

from django.conf import settings
from django.contrib.auth import get_user_model
from rest_framework.authtoken.models import Token

from apps.authentication.models import AuthProvider, UserProfile

logger = logging.getLogger(__name__)
User = get_user_model()


def _http_request(
    url: str,
    method: str = "GET",
    data: dict[str, Any] | None = None,
    headers: dict[str, str] | None = None,
) -> dict[str, Any]:
    req_headers = {
        "Accept": "application/json",
        "User-Agent": "CodeScope-Backend",
        **(headers or {}),
    }
    encoded_data = None
    if data is not None:
        if req_headers.get("Content-Type") == "application/json":
            encoded_data = json.dumps(data).encode("utf-8")
        else:
            req_headers["Content-Type"] = "application/x-www-form-urlencoded"
            encoded_data = urllib.parse.urlencode(data).encode("utf-8")

    req = urllib.request.Request(url, data=encoded_data, headers=req_headers, method=method)
    try:
        with urllib.request.urlopen(req, timeout=15) as response:
            res_body = response.read().decode("utf-8")
            return json.loads(res_body)
    except urllib.error.HTTPError as err:
        error_body = err.read().decode("utf-8", errors="replace")
        logger.warning("OAuth HTTP error %s from %s: %s", err.code, url, error_body)
        try:
            parsed = json.loads(error_body)
            raise ValueError(parsed.get("error_description") or parsed.get("error") or f"OAuth HTTP {err.code}")
        except json.JSONDecodeError:
            raise ValueError(f"OAuth HTTP {err.code}: {error_body[:200]}")
    except Exception as exc:
        logger.exception("OAuth network request failed: %s", exc)
        raise ValueError(f"OAuth request failed: {exc}")


def get_or_create_social_user(
    provider: str,
    provider_id: str,
    email: str,
    preferred_username: str,
    full_name: str = "",
    avatar_url: str = "",
) -> Tuple[Any, str, bool]:
    """Retrieve or create a Django user for an OAuth identity."""
    profile = UserProfile.objects.filter(provider=provider, provider_id=str(provider_id)).first()
    if profile:
        user = profile.user
        if avatar_url and profile.avatar_url != avatar_url:
            profile.avatar_url = avatar_url
            profile.save(update_fields=["avatar_url", "updated_at"])
        token, _ = Token.objects.get_or_create(user=user)
        return user, token.key, False

    user = None
    if email:
        user = User.objects.filter(email__iexact=email).first()

    created = False
    if not user:
        base_username = (preferred_username or email.split("@")[0] or "user").strip().lower()
        # Clean non-alphanumeric chars
        base_username = "".join(c for c in base_username if c.isalnum() or c in "_-") or "user"
        candidate_username = base_username
        n = 1
        while User.objects.filter(username=candidate_username).exists():
            n += 1
            candidate_username = f"{base_username}_{n}"

        first_name = full_name.split()[0] if full_name else ""
        last_name = " ".join(full_name.split()[1:]) if full_name and len(full_name.split()) > 1 else ""

        user = User.objects.create_user(
            username=candidate_username,
            email=email,
            first_name=first_name[:150],
            last_name=last_name[:150],
        )
        user.set_unusable_password()
        user.save()
        created = True

    profile, _ = UserProfile.objects.get_or_create(
        user=user,
        defaults={
            "provider": provider,
            "provider_id": str(provider_id),
            "avatar_url": avatar_url,
            "github_username": preferred_username if provider == AuthProvider.GITHUB else "",
        },
    )
    if not profile.avatar_url and avatar_url:
        profile.avatar_url = avatar_url
        profile.save(update_fields=["avatar_url", "updated_at"])

    token, _ = Token.objects.get_or_create(user=user)
    return user, token.key, created


def exchange_github_oauth(code: str, redirect_uri: str | None = None) -> Tuple[Any, str, bool]:
    client_id = getattr(settings, "GITHUB_CLIENT_ID", "")
    client_secret = getattr(settings, "GITHUB_CLIENT_SECRET", "")
    if not client_id or not client_secret:
        raise ValueError("GitHub OAuth is not configured on the server (GITHUB_CLIENT_ID / GITHUB_CLIENT_SECRET missing).")

    payload: dict[str, Any] = {
        "client_id": client_id,
        "client_secret": client_secret,
        "code": code,
    }
    if redirect_uri:
        payload["redirect_uri"] = redirect_uri

    token_res = _http_request(
        "https://github.com/login/oauth/access_token",
        method="POST",
        data=payload,
    )
    access_token = token_res.get("access_token")
    if not access_token:
        err_msg = token_res.get("error_description") or token_res.get("error") or "Failed to obtain GitHub access token"
        raise ValueError(err_msg)

    user_info = _http_request(
        "https://api.github.com/user",
        headers={"Authorization": f"Bearer {access_token}"},
    )
    gh_id = user_info.get("id")
    gh_login = user_info.get("login") or f"gh_{gh_id}"
    gh_name = user_info.get("name") or gh_login
    gh_email = user_info.get("email") or ""
    gh_avatar = user_info.get("avatar_url") or ""

    if not gh_email:
        try:
            emails = _http_request(
                "https://api.github.com/user/emails",
                headers={"Authorization": f"Bearer {access_token}"},
            )
            if isinstance(emails, list):
                primary = next((e for e in emails if e.get("primary") and e.get("verified")), None)
                if not primary and emails:
                    primary = emails[0]
                if primary:
                    gh_email = primary.get("email") or ""
        except Exception as exc:
            logger.warning("Could not fetch private GitHub emails: %s", exc)

    if not gh_email:
        gh_email = f"{gh_login}@users.noreply.github.com"

    return get_or_create_social_user(
        provider=AuthProvider.GITHUB,
        provider_id=str(gh_id),
        email=gh_email,
        preferred_username=gh_login,
        full_name=gh_name,
        avatar_url=gh_avatar,
    )


def exchange_google_oauth(
    code: str | None = None,
    id_token_str: str | None = None,
    redirect_uri: str | None = None,
) -> Tuple[Any, str, bool]:
    client_id = getattr(settings, "GOOGLE_CLIENT_ID", "")
    client_secret = getattr(settings, "GOOGLE_CLIENT_SECRET", "")

    if id_token_str:
        # Verify ID token directly with Google tokeninfo endpoint
        token_info = _http_request(
            f"https://oauth2.googleapis.com/tokeninfo?id_token={urllib.parse.quote(id_token_str)}"
        )
        if client_id and token_info.get("aud") != client_id:
            logger.warning("Google ID token aud mismatch (got %s, expected %s)", token_info.get("aud"), client_id)
        
        google_id = token_info.get("sub")
        email = token_info.get("email") or ""
        name = token_info.get("name") or email.split("@")[0]
        avatar = token_info.get("picture") or ""
        
        if not google_id or not email:
            raise ValueError("Invalid Google token: missing email or user ID.")

        return get_or_create_social_user(
            provider=AuthProvider.GOOGLE,
            provider_id=str(google_id),
            email=email,
            preferred_username=email.split("@")[0],
            full_name=name,
            avatar_url=avatar,
        )

    if code:
        if not client_id or not client_secret:
            raise ValueError("Google OAuth is not configured on the server (GOOGLE_CLIENT_ID / GOOGLE_CLIENT_SECRET missing).")

        payload: dict[str, Any] = {
            "client_id": client_id,
            "client_secret": client_secret,
            "code": code,
            "grant_type": "authorization_code",
            "redirect_uri": redirect_uri or "",
        }
        token_res = _http_request(
            "https://oauth2.googleapis.com/token",
            method="POST",
            data=payload,
        )
        access_token = token_res.get("access_token")
        if not access_token:
            err_msg = token_res.get("error_description") or token_res.get("error") or "Failed to exchange Google OAuth code"
            raise ValueError(err_msg)

        user_info = _http_request(
            "https://www.googleapis.com/oauth2/v3/userinfo",
            headers={"Authorization": f"Bearer {access_token}"},
        )
        google_id = user_info.get("sub")
        email = user_info.get("email") or ""
        name = user_info.get("name") or email.split("@")[0]
        avatar = user_info.get("picture") or ""

        if not google_id or not email:
            raise ValueError("Google user profile missing email or ID.")

        return get_or_create_social_user(
            provider=AuthProvider.GOOGLE,
            provider_id=str(google_id),
            email=email,
            preferred_username=email.split("@")[0],
            full_name=name,
            avatar_url=avatar,
        )

    raise ValueError("Either 'code' or 'id_token' must be provided for Google authentication.")
