from django.contrib import admin

from apps.projects.models import Project, ProjectFile, ProjectLanguage, ProjectSource


@admin.register(Project)
class ProjectAdmin(admin.ModelAdmin):
    list_display = ("name", "slug", "status", "file_count", "loc_total", "created_at")
    list_filter = ("status", "visibility")
    search_fields = ("name", "slug", "description")


@admin.register(ProjectSource)
class ProjectSourceAdmin(admin.ModelAdmin):
    list_display = ("project", "source_type", "original_filename", "github_url", "created_at")
    list_filter = ("source_type",)


@admin.register(ProjectFile)
class ProjectFileAdmin(admin.ModelAdmin):
    list_display = ("relative_path", "project", "language", "line_count", "is_test")
    list_filter = ("language", "is_test", "is_generated")
    search_fields = ("relative_path",)


@admin.register(ProjectLanguage)
class ProjectLanguageAdmin(admin.ModelAdmin):
    list_display = ("project", "language", "file_count", "loc")
