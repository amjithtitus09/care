import logging
from datetime import datetime
from typing import Any

from django.conf import settings
from django.db import transaction
from django.db.models import Q

from odoo.connector.jsonrpc import OdooJSONRPCConnection
from odoo.resource.invoice import OdooInvoiceResource

logger = logging.getLogger(__name__)


class OdooIntegrationError(Exception):
    """Base exception for Odoo integration errors"""


class OdooIntegrationService:
    """
    Service class for integrating Django Care application with Odoo.
    This class handles the synchronization of accounting data between
    the two systems.
    """

    def __init__(self):
        """Initialize the Odoo integration service."""
        self.connection = None
        self.invoice_resource = None
        self._initialize_connection()

    def _initialize_connection(self) -> None:
        """Initialize the Odoo connection and resources."""
        try:
            # Get Odoo configuration from Django settings
            odoo_config = getattr(settings, "ODOO_CONFIG", {})

            if not odoo_config:
                logger.warning(
                    "ODOO_CONFIG not found in settings. Odoo integration disabled."
                )
                return

            # Create connection
            self.connection = OdooJSONRPCConnection(
                base_url=odoo_config.get("base_url"),
                database=odoo_config.get("database"),
                username=odoo_config.get("username"),
                password=odoo_config.get("password"),
                timeout=odoo_config.get("timeout", 30),
                max_retries=odoo_config.get("max_retries", 3),
                cache_timeout=odoo_config.get("cache_timeout", 3600),
            )

            # Test connection
            if not self.connection.test_connection():
                logger.error("Failed to connect to Odoo. Integration disabled.")
                return

            # Initialize resources
            self.invoice_resource = OdooInvoiceResource(self.connection)

            logger.info("Odoo integration initialized successfully")

        except Exception as e:
            logger.error(f"Failed to initialize Odoo integration: {e!s}")
            self.connection = None
            self.invoice_resource = None

    def is_enabled(self) -> bool:
        """Check if Odoo integration is enabled and working."""
        return (
            self.connection is not None
            and self.invoice_resource is not None
            and self.connection.is_authenticated()
        )

    def sync_invoice_to_odoo(self, invoice_id: str) -> int | None:
        """
        Synchronize a Django invoice to Odoo.

        Args:
            invoice_id: External ID of the Django invoice

        Returns:
            Odoo invoice ID if successful, None otherwise
        """
        from care.emr.models.invoice import Invoice

        if not self.is_enabled():
            logger.warning("Odoo integration is not enabled")
            return None

        try:
            with transaction.atomic():
                # Get the Django invoice
                invoice = Invoice.objects.select_related(
                    "facility", "patient", "account"
                ).get(external_id=invoice_id)

                # Check if invoice already exists in Odoo
                odoo_invoice_id = self._get_odoo_invoice_id(invoice)
                if odoo_invoice_id:
                    logger.info(
                        f"Invoice {invoice_id} already exists in Odoo with ID: {odoo_invoice_id}"
                    )
                    return odoo_invoice_id

                # Create or get partner in Odoo
                partner_id = self._get_or_create_partner(
                    invoice.patient, invoice.facility
                )

                # Prepare invoice lines
                invoice_lines = self._prepare_invoice_lines(invoice)

                # Create invoice in Odoo
                odoo_invoice_id = self.invoice_resource.create_invoice(
                    partner_id=partner_id,
                    invoice_date=invoice.issue_date or datetime.now(),
                    invoice_lines=invoice_lines,
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

    def _get_odoo_invoice_id(self, invoice) -> int | None:
        """
        Get the Odoo invoice ID if it already exists.

        Args:
            invoice: Django invoice instance

        Returns:
            Odoo invoice ID if found, None otherwise
        """
        # Check if we have the Odoo ID stored in meta
        if invoice.meta and "odoo_invoice_id" in invoice.meta:
            odoo_id = invoice.meta["odoo_invoice_id"]
            # Verify it still exists in Odoo
            if self.invoice_resource.exists(odoo_id):
                return odoo_id

        # Try to find by reference number
        if invoice.number:
            try:
                invoices = self.invoice_resource.search(
                    domain=[("ref", "=", invoice.number)], limit=1
                )
                if invoices:
                    return invoices[0]["id"]
            except Exception as e:
                logger.warning(f"Failed to search for invoice by reference: {e!s}")

        return None

    def _get_or_create_partner(self, patient, facility) -> int:
        """
        Get or create a partner in Odoo for the patient/facility.

        Args:
            patient: Django patient instance
            facility: Django facility instance

        Returns:
            Odoo partner ID
        """
        # For now, we'll use a simple approach - create partner based on patient
        # In a real implementation, you might want to create partners for both
        # patients and facilities, or use a more sophisticated mapping

        partner_name = f"{patient.name} - {facility.name}"

        try:
            # Search for existing partner
            partners = self.connection.search_read(
                "res.partner", [("name", "=", partner_name)], fields=["id"], limit=1
            )

            if partners:
                return partners[0]["id"]

            # Create new partner
            partner_data = {
                "name": partner_name,
                "is_company": False,
                "customer_rank": 1,  # Mark as customer
                "supplier_rank": 0,
                "phone": str(patient.phone_number) if patient.phone_number else None,
                "street": patient.address,
            }

            partner_id = self.connection.create_record("res.partner", partner_data)
            logger.info(f"Created new partner in Odoo with ID: {partner_id}")
            return partner_id

        except Exception as e:
            logger.error(f"Failed to get or create partner: {e!s}")
            # Return a default partner ID or raise an error
            raise OdooIntegrationError(f"Failed to get or create partner: {e!s}")

    def _prepare_invoice_lines(self, invoice) -> list[dict[str, Any]]:
        """
        Prepare invoice lines for Odoo from Django charge items.

        Args:
            invoice: Django invoice instance

        Returns:
            List of invoice line dictionaries
        """
        invoice_lines = []
        from care.emr.models.charge_item import ChargeItem

        # Get charge items for this invoice
        charge_items = ChargeItem.objects.filter(
            id__in=invoice.charge_items
        ).select_related("charge_item_definition")

        for charge_item in charge_items:
            # Get or create product in Odoo
            product_id = self._get_or_create_product(charge_item)

            # Calculate line amounts
            quantity = float(charge_item.quantity or 1.0)
            price_unit = float(charge_item.total_price or 0.0) / quantity

            line_data = {
                "product_id": product_id,
                "name": charge_item.title or charge_item.description or "Service",
                "quantity": quantity,
                "price_unit": price_unit,
            }

            # Add tax information if available
            if charge_item.total_price_components:
                tax_ids = self._get_tax_ids(charge_item.total_price_components)
                if tax_ids:
                    line_data["tax_ids"] = tax_ids

            invoice_lines.append(line_data)

        return invoice_lines

    def _get_or_create_product(self, charge_item) -> int:
        """
        Get or create a product in Odoo for the charge item.

        Args:
            charge_item: Django charge item instance

        Returns:
            Odoo product ID
        """
        product_name = charge_item.title or "Service"

        try:
            # Search for existing product
            products = self.connection.search_read(
                "product.product", [("name", "=", product_name)], fields=["id"], limit=1
            )

            if products:
                return products[0]["id"]

            # Create new product
            product_data = {
                "name": product_name,
                "type": "service",  # Most charge items are services
                "categ_id": 1,  # Default category
                "list_price": float(charge_item.total_price or 0.0),
                "standard_price": float(charge_item.total_price or 0.0),
                "default_code": f"CHG_{charge_item.id}",
            }

            product_id = self.connection.create_record("product.product", product_data)
            logger.info(f"Created new product in Odoo with ID: {product_id}")
            return product_id

        except Exception as e:
            logger.error(f"Failed to get or create product: {e!s}")
            # Return a default product ID
            return 1  # Default product ID

    def _get_tax_ids(self, price_components: list[dict[str, Any]]) -> list[int]:
        """
        Get tax IDs from price components.

        Args:
            price_components: List of price component dictionaries

        Returns:
            List of tax IDs
        """
        tax_ids = []

        for component in price_components:
            if component.get("monetary_component_type") == "tax":
                # Try to find tax by code
                tax_code = component.get("code", {}).get("code")
                if tax_code:
                    try:
                        taxes = self.connection.search_read(
                            "account.tax",
                            [("name", "ilike", tax_code)],
                            fields=["id"],
                            limit=1,
                        )
                        if taxes:
                            tax_ids.append(taxes[0]["id"])
                    except Exception as e:
                        logger.warning(f"Failed to find tax for code {tax_code}: {e!s}")

        return tax_ids

    def sync_invoice_status(self, invoice_id: str) -> bool:
        """
        Synchronize invoice status from Odoo to Django.

        Args:
            invoice_id: External ID of the Django invoice

        Returns:
            True if synchronization was successful
        """
        from care.emr.models.invoice import Invoice

        if not self.is_enabled():
            logger.warning("Odoo integration is not enabled")
            return False

        try:
            invoice = Invoice.objects.get(external_id=invoice_id)

            # Get Odoo invoice ID
            odoo_invoice_id = invoice.meta.get("odoo_invoice_id")
            if not odoo_invoice_id:
                logger.warning(f"No Odoo invoice ID found for invoice {invoice_id}")
                return False

            # Get invoice status from Odoo
            odoo_invoice = self.invoice_resource.read(
                odoo_invoice_id, fields=["state", "payment_state"]
            )

            # Map Odoo status to Django status
            odoo_state = odoo_invoice.get("state", "draft")
            payment_state = odoo_invoice.get("payment_state", "not_paid")

            # Update Django invoice status
            if odoo_state == "posted" and payment_state == "paid":
                invoice.status = "paid"
            elif odoo_state == "posted":
                invoice.status = "posted"
            elif odoo_state == "cancelled":
                invoice.status = "cancelled"
            else:
                invoice.status = "draft"

            invoice.save(update_fields=["status"])

            logger.info(f"Updated invoice {invoice_id} status to: {invoice.status}")
            return True

        except Invoice.DoesNotExist:
            logger.error(f"Invoice {invoice_id} not found")
            return False
        except Exception as e:
            logger.error(f"Failed to sync invoice status: {e!s}")
            return False

    def sync_all_invoices(self, limit: int | None = None) -> dict[str, Any]:
        """
        Synchronize all invoices from Django to Odoo.

        Args:
            limit: Maximum number of invoices to sync

        Returns:
            Dictionary with sync results
        """
        from care.emr.models.invoice import Invoice

        if not self.is_enabled():
            logger.warning("Odoo integration is not enabled")
            return {"success": False, "message": "Integration not enabled"}

        results = {"total": 0, "success": 0, "failed": 0, "errors": []}

        try:
            # Get invoices that haven't been synced yet
            invoices = Invoice.objects.filter(
                Q(meta__isnull=True) | ~Q(meta__has_key="odoo_invoice_id")
            )

            if limit:
                invoices = invoices[:limit]

            results["total"] = invoices.count()

            for invoice in invoices:
                try:
                    odoo_id = self.sync_invoice_to_odoo(str(invoice.external_id))
                    if odoo_id:
                        results["success"] += 1
                    else:
                        results["failed"] += 1
                        results["errors"].append(
                            f"Failed to sync invoice {invoice.external_id}"
                        )
                except Exception as e:
                    results["failed"] += 1
                    results["errors"].append(
                        f"Error syncing invoice {invoice.external_id}: {e!s}"
                    )

            logger.info(
                f"Sync completed: {results['success']} successful, {results['failed']} failed"
            )
            return results

        except Exception as e:
            logger.error(f"Failed to sync invoices: {e!s}")
            return {"success": False, "message": str(e)}

    def validate_odoo_invoice(self, invoice_id: str) -> bool:
        """
        Validate (post) an invoice in Odoo.

        Args:
            invoice_id: External ID of the Django invoice

        Returns:
            True if validation was successful
        """
        from care.emr.models.invoice import Invoice

        if not self.is_enabled():
            logger.warning("Odoo integration is not enabled")
            return False

        try:
            invoice = Invoice.objects.get(external_id=invoice_id)
            odoo_invoice_id = invoice.meta.get("odoo_invoice_id")

            if not odoo_invoice_id:
                logger.warning(f"No Odoo invoice ID found for invoice {invoice_id}")
                return False

            success = self.invoice_resource.validate_invoice(odoo_invoice_id)

            if success:
                logger.info(f"Validated invoice {invoice_id} in Odoo")
                # Update Django invoice status
                invoice.status = "posted"
                invoice.save(update_fields=["status"])

            return success

        except Invoice.DoesNotExist:
            logger.error(f"Invoice {invoice_id} not found")
            return False
        except Exception as e:
            logger.error(f"Failed to validate invoice: {e!s}")
            return False


# Global instance of the integration service
