import logging

from care.emr.models.invoice import Invoice
from odoo.resource.base import OdooBaseResource

logger = logging.getLogger(__name__)


class OdooInvoiceResource(OdooBaseResource):
    resource_name = "account.move"

    def find_by_care_id(self, care_id: str):
        """
        Find a partner by Care ID.
        """
        model = self.get_odoo_model()
        results = model.search([("x_care_id", "=", care_id)], limit=1)
        if results and len(results) != 0:
            return results[0]
        return None

    def create_invoice(self, invoice, partner_id) -> int:
        # Prepare invoice data
        from odoo.resource.currency import OdooCurrencyResource
        from odoo.resource.state import OdooStateResource

        invoice_data = {
            "name": invoice.number,
            "partner_id": partner_id,
            "invoice_date": invoice.created_date.strftime("%Y-%m-%d"),
            "move_type": "out_invoice",
            "x_care_id": str(invoice.external_id),
            "invoice_line_ids": [],
            "ref": invoice.number,
            "currency_id": OdooCurrencyResource().get_currency_id("INR"),
            # "company_id": None,
            "l10n_in_state_id": OdooStateResource().get_state_id("Kerala"),
            "narration": None,
            "payment_reference": None,
            "invoice_payment_term_id": None,
            "fiscal_position_id": None,
        }

        # Create the invoice
        invoice = self.find_by_care_id(str(invoice.external_id))
        if not invoice:
            invoice = self.get_odoo_model().create(invoice_data)

        logger.info(f"Created invoice with ID: {invoice}")
        return invoice

    def check_by_care_id(self, care_id: str) -> bool:
        """
        Check if an invoice exists in Odoo by Care ID.
        """
        return

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
        from odoo.resource.partner import OdooPartnerResource

        # Get the Django invoice
        invoice = Invoice.objects.select_related("facility", "patient", "account").get(
            external_id=invoice_id
        )

        partner = OdooPartnerResource().get_or_create_patient_partner(invoice.patient)

        # Create invoice in Odoo
        odoo_invoice_id = self.create_invoice(invoice, partner)

        logger.info(
            f"Successfully synced invoice {invoice_id} to Odoo with ID: {odoo_invoice_id}"
        )
        return odoo_invoice_id
