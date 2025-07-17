from django.core.management.base import BaseCommand
from django.db import transaction
from django.db.models import Q

from odoo.integration import odoo_integration


class Command(BaseCommand):
    help = "Synchronize invoices from Django to Odoo"

    def add_arguments(self, parser):
        parser.add_argument(
            "--invoice-id",
            type=str,
            help="Sync specific invoice by external ID",
        )
        parser.add_argument(
            "--limit",
            type=int,
            help="Maximum number of invoices to sync",
        )
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Show what would be synced without actually syncing",
        )
        parser.add_argument(
            "--force",
            action="store_true",
            help="Force sync even if invoice already exists in Odoo",
        )

    def handle(self, *args, **options):
        invoice_id = options["invoice_id"]
        limit = options["limit"]
        dry_run = options["dry_run"]
        force = options["force"]

        self.stdout.write(self.style.SUCCESS("Odoo Invoice Synchronization"))
        self.stdout.write("=" * 50)

        # Check if Odoo integration is enabled
        if not odoo_integration.is_enabled():
            self.stdout.write(self.style.ERROR("❌ Odoo integration is not enabled"))
            return

        if invoice_id:
            # Sync specific invoice
            self._sync_single_invoice(invoice_id, dry_run, force)
        else:
            # Sync all invoices
            self._sync_all_invoices(limit, dry_run, force)

        self.stdout.write("=" * 50)
        self.stdout.write("Synchronization completed.")

    def _sync_single_invoice(self, invoice_id: str, dry_run: bool, force: bool):
        """Sync a single invoice."""
        # Import here to avoid circular imports
        from care.emr.models.invoice import Invoice

        self.stdout.write(f"Syncing invoice: {invoice_id}")

        try:
            # Check if invoice exists in Django
            try:
                invoice = Invoice.objects.get(external_id=invoice_id)
            except Invoice.DoesNotExist:
                self.stdout.write(
                    self.style.ERROR(f"❌ Invoice {invoice_id} not found in Django")
                )
                return

            # Check if already synced to Odoo
            odoo_invoice_id = None
            if invoice.meta and "odoo_invoice_id" in invoice.meta:
                odoo_invoice_id = invoice.meta["odoo_invoice_id"]
                if not force:
                    self.stdout.write(
                        self.style.WARNING(
                            f"⚠️  Invoice already synced to Odoo (ID: {odoo_invoice_id})"
                        )
                    )
                    self.stdout.write("Use --force to re-sync")
                    return

            if dry_run:
                self.stdout.write(
                    self.style.SUCCESS(f"✅ Would sync invoice {invoice_id} to Odoo")
                )
                self.stdout.write(f"  Title: {invoice.title}")
                self.stdout.write(f"  Patient: {invoice.patient.name}")
                self.stdout.write(f"  Facility: {invoice.facility.name}")
                self.stdout.write(f"  Amount: {invoice.total_gross}")
                return

            # Actually sync the invoice
            with transaction.atomic():
                odoo_id = odoo_integration.sync_invoice_to_odoo(invoice_id)

                if odoo_id:
                    self.stdout.write(
                        self.style.SUCCESS(
                            f"✅ Successfully synced invoice {invoice_id} to Odoo (ID: {odoo_id})"
                        )
                    )
                else:
                    self.stdout.write(
                        self.style.ERROR(
                            f"❌ Failed to sync invoice {invoice_id} to Odoo"
                        )
                    )

        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f"❌ Error syncing invoice {invoice_id}: {e!s}")
            )

    def _sync_all_invoices(self, limit: int, dry_run: bool, force: bool):
        """Sync all invoices."""
        # Import here to avoid circular imports
        from care.emr.models.invoice import Invoice

        self.stdout.write("Syncing all invoices...")

        # Get invoices that haven't been synced yet
        invoices = Invoice.objects.filter(
            Q(meta__isnull=True) | ~Q(meta__has_key="odoo_invoice_id")
        )

        if limit:
            invoices = invoices[:limit]

        total_count = invoices.count()
        self.stdout.write(f"Found {total_count} invoices to sync")

        if dry_run:
            self.stdout.write("DRY RUN - No actual syncing will be performed")
            self.stdout.write("")

            for i, invoice in enumerate(invoices, 1):
                self.stdout.write(
                    f"{i}. {invoice.external_id} - {invoice.title} - {invoice.total_gross}"
                )

            return

        # Actually sync invoices
        success_count = 0
        error_count = 0

        for i, invoice in enumerate(invoices, 1):
            self.stdout.write(
                f"[{i}/{total_count}] Syncing invoice {invoice.external_id}..."
            )

            try:
                odoo_id = odoo_integration.sync_invoice_to_odoo(
                    str(invoice.external_id)
                )

                if odoo_id:
                    self.stdout.write(
                        self.style.SUCCESS(f"  ✅ Success (Odoo ID: {odoo_id})")
                    )
                    success_count += 1
                else:
                    self.stdout.write(self.style.ERROR("  ❌ Failed"))
                    error_count += 1

            except Exception as e:
                self.stdout.write(self.style.ERROR(f"  ❌ Error: {e!s}"))
                error_count += 1

        # Summary
        self.stdout.write("")
        self.stdout.write("Sync Summary:")
        self.stdout.write(f"  Total: {total_count}")
        self.stdout.write(f"  Success: {success_count}")
        self.stdout.write(f"  Errors: {error_count}")

        if success_count > 0:
            self.stdout.write(
                self.style.SUCCESS(f"✅ Successfully synced {success_count} invoices")
            )

        if error_count > 0:
            self.stdout.write(
                self.style.ERROR(f"❌ Failed to sync {error_count} invoices")
            )
