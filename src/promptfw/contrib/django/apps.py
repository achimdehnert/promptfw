from django.apps import AppConfig
from django.utils.translation import gettext_lazy as _


class PromptfwConfig(AppConfig):
    name = "promptfw.contrib.django"
    label = "promptfw"
    verbose_name = _("Prompt Framework")
    default_auto_field = "django.db.models.BigAutoField"
