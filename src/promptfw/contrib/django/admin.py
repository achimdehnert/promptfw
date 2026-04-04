"""
PromptTemplate Admin — CRUD, soft-delete, versioning, cache invalidation (ADR-146).
"""

import uuid

from django.contrib import admin
from django.db import transaction
from django.utils.translation import gettext_lazy as _

from promptfw.contrib.django.models import PromptTemplate
from promptfw.contrib.django.resolution import invalidate_cache


@admin.register(PromptTemplate)
class PromptTemplateAdmin(admin.ModelAdmin):
    list_display = [
        "action_code",
        "version",
        "name",
        "hub",
        "domain",
        "is_active",
        "updated_at",
    ]
    list_filter = ["hub", "domain", "is_active", "response_format"]
    search_fields = [
        "action_code",
        "name",
        "description",
        "system_template",
        "user_template",
    ]
    readonly_fields = ["public_id", "created_at", "updated_at", "created_by"]

    fieldsets = [
        (
            _("Identity"),
            {"fields": ["action_code", "version", "name", "description", "public_id"]},
        ),
        (
            _("Content"),
            {
                "fields": ["system_template", "user_template"],
                "description": _(
                    "Jinja2 templates (SandboxedEnvironment). Variables: {{ var_name }}"
                ),
            },
        ),
        (
            _("Parametrization"),
            {
                "fields": ["defaults", "variables_schema"],
                "classes": ["collapse"],
            },
        ),
        (
            _("LLM Hints"),
            {
                "fields": [
                    "suggested_max_tokens",
                    "suggested_temperature",
                    "response_format",
                    "output_schema",
                ],
                "classes": ["collapse"],
            },
        ),
        (
            _("Metadata"),
            {"fields": ["hub", "domain", "tags", "notes", "is_active", "tenant_id"]},
        ),
        (
            _("Audit"),
            {"fields": ["created_by", "created_at", "updated_at", "deleted_at"]},
        ),
    ]

    def save_model(self, request, obj, form, change):
        if not change:
            obj.created_by = request.user.username
        super().save_model(request, obj, form, change)
        invalidate_cache(obj.action_code)

    def delete_model(self, request, obj):
        # Soft-delete instead of hard-delete
        from django.utils import timezone

        obj.deleted_at = timezone.now()
        obj.is_active = False
        obj.save(update_fields=["deleted_at", "is_active"])
        invalidate_cache(obj.action_code)

    def delete_queryset(self, request, queryset):
        # Bulk soft-delete (Admin "Delete selected" action)
        from django.utils import timezone

        action_codes = set(queryset.values_list("action_code", flat=True))
        queryset.update(deleted_at=timezone.now(), is_active=False)
        for ac in action_codes:
            invalidate_cache(ac)

    @admin.action(
        description=_("Create new version (copy with incremented version)")
    )
    def create_new_version(self, request, queryset):
        count = 0
        for tpl in queryset.filter(is_active=True):
            with transaction.atomic():
                new_version = tpl.version + 1
                # Deactivate old
                tpl.is_active = False
                tpl.save(update_fields=["is_active"])
                # Create new version as copy
                tpl.pk = None
                tpl.public_id = uuid.uuid4()
                tpl.version = new_version
                tpl.is_active = True
                tpl.created_by = request.user.username
                tpl.deleted_at = None
                tpl.save()
                invalidate_cache(tpl.action_code)
                count += 1
        self.message_user(request, _("%(count)d new version(s) created.") % {"count": count})

    actions = [create_new_version]
