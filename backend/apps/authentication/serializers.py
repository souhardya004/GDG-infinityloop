from __future__ import annotations

from django.contrib.auth import authenticate, get_user_model
from rest_framework import serializers

from apps.authentication.models import UserProfile

User = get_user_model()


class UserSerializer(serializers.ModelSerializer):
    avatar_url = serializers.SerializerMethodField()
    provider = serializers.SerializerMethodField()
    github_username = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = [
            "id",
            "username",
            "email",
            "first_name",
            "last_name",
            "avatar_url",
            "provider",
            "github_username",
            "date_joined",
        ]
        read_only_fields = fields

    def get_avatar_url(self, obj: User) -> str:
        profile = getattr(obj, "profile", None)
        return profile.avatar_url if profile else ""

    def get_provider(self, obj: User) -> str:
        profile = getattr(obj, "profile", None)
        return profile.provider if profile else "email"

    def get_github_username(self, obj: User) -> str:
        profile = getattr(obj, "profile", None)
        return profile.github_username if profile else ""


class LoginSerializer(serializers.Serializer):
    username_or_email = serializers.CharField(required=True)
    password = serializers.CharField(required=True, write_only=True)

    def validate(self, attrs):
        identifier = attrs.get("username_or_email", "").strip()
        password = attrs.get("password", "")

        # Support login by email or username
        user = None
        if "@" in identifier:
            user_obj = User.objects.filter(email__iexact=identifier).first()
            if user_obj:
                user = authenticate(username=user_obj.username, password=password)
        if not user:
            user = authenticate(username=identifier, password=password)

        if not user:
            raise serializers.ValidationError("Invalid username/email or password.")
        if not user.is_active:
            raise serializers.ValidationError("This user account is inactive.")

        attrs["user"] = user
        return attrs


class SignupSerializer(serializers.Serializer):
    username = serializers.CharField(max_length=150, required=False, allow_blank=True)
    email = serializers.EmailField(required=True)
    password = serializers.CharField(min_length=6, write_only=True, required=True)
    full_name = serializers.CharField(max_length=150, required=False, allow_blank=True, default="")

    def validate_email(self, value):
        if User.objects.filter(email__iexact=value).exists():
            raise serializers.ValidationError("A user with this email already exists.")
        return value.lower().strip()

    def validate_username(self, value):
        val = (value or "").strip()
        if val and User.objects.filter(username__iexact=val).exists():
            raise serializers.ValidationError("This username is already taken.")
        return val

    def create(self, validated_data):
        email = validated_data["email"]
        raw_username = validated_data.get("username")
        if not raw_username:
            base = email.split("@")[0]
            base = "".join(c for c in base if c.isalnum() or c in "_-") or "user"
            cand = base
            n = 1
            while User.objects.filter(username=cand).exists():
                n += 1
                cand = f"{base}_{n}"
            raw_username = cand

        full_name = validated_data.get("full_name", "").strip()
        first_name = full_name.split()[0] if full_name else ""
        last_name = " ".join(full_name.split()[1:]) if full_name and len(full_name.split()) > 1 else ""

        user = User.objects.create_user(
            username=raw_username,
            email=email,
            password=validated_data["password"],
            first_name=first_name,
            last_name=last_name,
        )
        UserProfile.objects.create(user=user, provider="email")
        return user


class GitHubAuthSerializer(serializers.Serializer):
    code = serializers.CharField(required=True)
    redirect_uri = serializers.CharField(required=False, allow_blank=True, default="")


class GoogleAuthSerializer(serializers.Serializer):
    code = serializers.CharField(required=False, allow_blank=True, default="")
    id_token = serializers.CharField(required=False, allow_blank=True, default="")
    redirect_uri = serializers.CharField(required=False, allow_blank=True, default="")

    def validate(self, attrs):
        if not attrs.get("code") and not attrs.get("id_token"):
            raise serializers.ValidationError("Either 'code' or 'id_token' is required for Google login.")
        return attrs
