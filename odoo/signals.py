from django.db.models.signals import post_save
from django.dispatch import receiver

from care.emr.models.invoice import Invoice
from care.emr.resources.invoice.spec import InvoiceStatusOptions
from odoo.resource.invoice import OdooInvoiceResource


@receiver(post_save, sender=Invoice)
def save_fields_before_update(sender, instance, raw, using, update_fields, **kwargs):
    if instance.status in [
        InvoiceStatusOptions.issued.value,
        InvoiceStatusOptions.balanced.value,
    ]:
        odoo_integration = OdooInvoiceResource()
        odoo_integration.sync_invoice_to_odoo(instance.external_id)
