import logging

from django.core.management.base import BaseCommand

from odoo.resource.invoice import OdooInvoiceResource


class Command(BaseCommand):
    help = "Sync a specific invoice from Care to Odoo"

    def add_arguments(self, parser):
        parser.add_argument(
            "--force",
            action="store_true",
            help="Force sync even if invoice already exists in Odoo",
        )
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Show what would be synced without actually syncing",
        )
        parser.add_argument(
            "--validate",
            action="store_true",
            help="Validate (post) the invoice in Odoo after syncing",
        )
        parser.add_argument(
            "--verbose",
            action="store_true",
            help="Show detailed information about the sync process",
        )

    def handle(self, *args, **options):
        invoice_id = "b1d9bf54-d61f-4f83-9767-2617a15cd19b"
        logging.info("Starting to Sync Invoice %s", invoice_id)

        odoo_integration = OdooInvoiceResource()
        odoo_integration.sync_invoice_to_odoo(invoice_id)
