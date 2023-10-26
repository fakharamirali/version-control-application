from django.apps import AppConfig
from django.utils.translation import gettext_lazy as _


class VcaConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "VCA"
    verbose_name = _("Version Control Application")
