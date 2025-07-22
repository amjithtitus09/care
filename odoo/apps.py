from django.apps import AppConfig
from django.utils.translation import gettext_lazy as _


class OdooConfig(AppConfig):
    name = "odoo"
    verbose_name = _("Odoo")

    def ready(self):
        import odoo.signals  # noqa
