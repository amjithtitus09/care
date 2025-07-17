import logging
from datetime import datetime

from django.db import transaction

from odoo.integration.base import OdooIntegration
from odoo.resource.invoice import OdooInvoiceResource
from odoo.resource.partner import OdooPartnerResource

logger = logging.getLogger(__name__)


class OdooInvoiceIntegration(OdooIntegration):
    resource = OdooInvoiceResource()
    partner_resource = OdooPartnerResource()

    def check_invoice_exists(self, invoice_id: str) -> bool:
        """
        Check if an invoice exists in Odoo.
        """
        return self.resource.check_by_care_id(invoice_id)

    def sync_invoice_to_odoo(self, invoice_id: str) -> int | None:
        """
        Synchronize a Django invoice to Odoo.

        Args:
            invoice_id: External ID of the Django invoice

        Returns:
            Odoo invoice ID if successful, None otherwise
        """
        from care.emr.models.invoice import Invoice

        try:
            with transaction.atomic():
                # Get the Django invoice
                invoice = Invoice.objects.select_related(
                    "facility", "patient", "account"
                ).get(external_id=invoice_id)

                partner = self.partner_resource.get_or_create_patient_partner(
                    invoice.patient
                )
                raise Exception(f"Partner: {partner}")

                # Create invoice in Odoo
                odoo_invoice_id = self.resource.create_invoice(
                    partner_id=partner_id,
                    invoice_date=invoice.issue_date or datetime.now(),
                    invoice_lines=[],
                    ref=invoice.number,
                    narration=invoice.note,
                    move_type="out_invoice",  # Customer invoice
                    payment_reference=invoice.number,
                )

                # Update Django invoice with Odoo reference
                invoice.meta["odoo_invoice_id"] = odoo_invoice_id
                invoice.save(update_fields=["meta"])

                logger.info(
                    f"Successfully synced invoice {invoice_id} to Odoo with ID: {odoo_invoice_id}"
                )
                return odoo_invoice_id

        except Invoice.DoesNotExist:
            logger.error(f"Invoice {invoice_id} not found in Django")
            return None
        except Exception as e:
            logger.error(f"Failed to sync invoice {invoice_id} to Odoo: {e!s}")
            return None
