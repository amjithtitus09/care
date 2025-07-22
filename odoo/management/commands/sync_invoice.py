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
        invoice_id = "b5c3eb84-8418-41af-a2bd-a960880e96d8"
        logging.info("Starting to Sync Invoice %s", invoice_id)

        odoo_integration = OdooInvoiceResource()
        odoo_integration.sync_invoice_to_odoo(invoice_id)
