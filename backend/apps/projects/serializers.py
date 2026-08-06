"""DRF serializers for projects and ingest."""

from __future__ import annotations

from rest_framework import serializers

from apps.projects.models import (
    Project,
    ProjectFile,
    ProjectLanguage,
    ProjectSource,
    ProjectVisibility,
)


class ProjectLanguageSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProjectLanguage
        fields = ("language", "file_count", "loc")


class ProjectStatsSerializer(serializers.Serializer):
    loc_total = serializers.IntegerField()
    file_count = serializers.IntegerField()
    function_count = serializers.IntegerField()
    class_count = serializers.IntegerField()
    api_count = serializers.IntegerField()
    table_count = serializers.IntegerField()
    technical_debt_score = serializers.DecimalField(
        max_digits=6, decimal_places=2, allow_null=True
    )
    architecture_pattern = serializers.CharField(allow_blank=True)


class ProjectSerializer(serializers.ModelSerializer):
    stats = serializers.SerializerMethodField()
    languages = ProjectLanguageSerializer(many=True, read_only=True)

    class Meta:
        model = Project
        fields = (
            "id",
            "name",
            "slug",
            "description",
            "status",
            "visibility",
            "stats",
            "languages",
            "analyzed_at",
            "created_at",
            "updated_at",
        )
        read_only_fields = (
            "id",
            "slug",
            "status",
            "analyzed_at",
            "created_at",
            "updated_at",
        )

    def get_stats(self, obj: Project) -> dict:
        return {
            "loc_total": obj.loc_total,
            "file_count": obj.file_count,
            "function_count": obj.function_count,
            "class_count": obj.class_count,
            "api_count": obj.api_count,
            "table_count": obj.table_count,
            "technical_debt_score": obj.technical_debt_score,
            "architecture_pattern": obj.architecture_pattern or None,
        }


class ProjectCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Project
        fields = ("name", "description", "visibility")

    def validate_name(self, value: str) -> str:
        cleaned = value.strip()
        if not cleaned:
            raise serializers.ValidationError("name must not be blank")
        return cleaned


class ProjectUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Project
        fields = ("name", "description", "visibility")

    def validate_name(self, value: str) -> str:
        cleaned = value.strip()
        if not cleaned:
            raise serializers.ValidationError("name must not be blank")
        return cleaned


class ProjectSummarySerializer(serializers.ModelSerializer):
    class Meta:
        model = Project
        fields = (
            "id",
            "name",
            "slug",
            "status",
            "visibility",
            "file_count",
            "loc_total",
            "created_at",
            "analyzed_at",
        )


class ProjectSourceSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProjectSource
        fields = (
            "id",
            "source_type",
            "original_filename",
            "github_url",
            "git_commit_sha",
            "size_bytes",
            "checksum_sha256",
            "created_at",
        )


class IngestGitHubSerializer(serializers.Serializer):
    url = serializers.URLField(max_length=500)
    branch = serializers.CharField(max_length=200, required=False, allow_blank=True)
    commit_sha = serializers.CharField(max_length=64, required=False, allow_blank=True)
    access_token = serializers.CharField(max_length=500, required=False, allow_blank=True)


class ProjectFileSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProjectFile
        fields = (
            "id",
            "relative_path",
            "language",
            "size_bytes",
            "line_count",
            "content_hash",
            "is_generated",
            "is_test",
            "created_at",
        )


class FileTreeNodeSerializer(serializers.Serializer):
    name = serializers.CharField()
    path = serializers.CharField()
    type = serializers.ChoiceField(choices=["folder", "file"])
    language = serializers.CharField(required=False, allow_blank=True)
    size_bytes = serializers.IntegerField(required=False)
    line_count = serializers.IntegerField(required=False)
    file_count = serializers.IntegerField(required=False)
    children = serializers.ListField(child=serializers.DictField(), required=False)
