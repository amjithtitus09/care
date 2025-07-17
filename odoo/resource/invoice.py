import logging
from datetime import datetime
from typing import Any

from odoo.resource.base import OdooResource, OdooResourceError

logger = logging.getLogger(__name__)


class OdooInvoiceResource(OdooResource):
    """
    Odoo resource for handling invoice operations (account.move model).
    This class provides methods to create, read, update, and delete invoices
    in Odoo with proper field mapping and validation.
    """

    _partner_cache = {}
    _product_cache = {}
    _tax_cache = {}

    MODEL_NAME = "account.move"

    # Fields for creating invoices
    CREATE_FIELDS = [
        "partner_id",
        "invoice_date",
        "invoice_due_date",
        "invoice_line_ids",
        "ref",
        "narration",
        "currency_id",
        "company_id",
        "move_type",
        "payment_reference",
        "invoice_payment_term_id",
        "fiscal_position_id",
    ]

    # Fields for updating invoices
    UPDATE_FIELDS = [
        "partner_id",
        "invoice_date",
        "invoice_due_date",
        "ref",
        "narration",
        "payment_reference",
        "invoice_payment_term_id",
        "fiscal_position_id",
    ]

    # Fields for reading invoices
    READ_FIELDS = [
        "id",
        "name",
        "partner_id",
        "invoice_date",
        "invoice_due_date",
        "amount_untaxed",
        "amount_tax",
        "amount_total",
        "amount_residual",
        "state",
        "move_type",
        "ref",
        "narration",
        "currency_id",
        "company_id",
        "payment_reference",
        "invoice_payment_term_id",
        "fiscal_position_id",
        "invoice_line_ids",
        "create_date",
        "write_date",
    ]

    # Default search domain for invoices
    DEFAULT_DOMAIN = [("move_type", "in", ["out_invoice", "in_invoice"])]

    # Default ordering
    DEFAULT_ORDER = "create_date desc"

    def create_invoice(
        self,
        partner_id: int,
        invoice_date: datetime,
        invoice_lines: list[dict[str, Any]],
        ref: str | None = None,
        narration: str | None = None,
        currency_id: int | None = None,
        company_id: int | None = None,
        move_type: str = "out_invoice",
        payment_reference: str | None = None,
        invoice_payment_term_id: int | None = None,
        fiscal_position_id: int | None = None,
        invoice_due_date: datetime | None = None,
    ) -> int:
        """
        Create a new invoice in Odoo.

        Args:
            partner_id: ID of the partner (customer/vendor)
            invoice_date: Date of the invoice
            invoice_lines: List of invoice line dictionaries
            ref: Reference number
            narration: Additional notes
            currency_id: Currency ID (defaults to company currency)
            company_id: Company ID (defaults to current company)
            move_type: Type of move ('out_invoice' for customer invoice, 'in_invoice' for vendor bill)
            payment_reference: Payment reference
            invoice_payment_term_id: Payment term ID
            fiscal_position_id: Fiscal position ID
            invoice_due_date: Due date for payment

        Returns:
            ID of the created invoice

        Raises:
            OdooResourceError: If creation fails
        """
        try:
            # Prepare invoice data
            invoice_data = {
                "partner_id": partner_id,
                "invoice_date": invoice_date.strftime("%Y-%m-%d")
                if invoice_date
                else None,
                "invoice_due_date": invoice_due_date.strftime("%Y-%m-%d")
                if invoice_due_date
                else None,
                "move_type": move_type,
            }

            # Add optional fields
            if ref:
                invoice_data["ref"] = ref
            if narration:
                invoice_data["narration"] = narration
            if currency_id:
                invoice_data["currency_id"] = currency_id
            if company_id:
                invoice_data["company_id"] = company_id
            if payment_reference:
                invoice_data["payment_reference"] = payment_reference
            if invoice_payment_term_id:
                invoice_data["invoice_payment_term_id"] = invoice_payment_term_id
            if fiscal_position_id:
                invoice_data["fiscal_position_id"] = fiscal_position_id
            if invoice_due_date:
                invoice_data["invoice_due_date"] = invoice_due_date.strftime("%Y-%m-%d")

            # Create invoice lines
            if invoice_lines:
                invoice_data["invoice_line_ids"] = self._prepare_invoice_lines(
                    invoice_lines
                )

            # Create the invoice
            invoice_id = self.create(invoice_data)

            logger.info(f"Created invoice with ID: {invoice_id}")
            return invoice_id

        except Exception as e:
            logger.error(f"Failed to create invoice: {e!s}")
            raise OdooResourceError(f"Failed to create invoice: {e!s}")

    def _prepare_invoice_lines(
        self, invoice_lines: list[dict[str, Any]]
    ) -> list[list[int, int, dict[str, Any]]]:
        """
        Prepare invoice lines for Odoo format.

        Args:
            invoice_lines: List of invoice line dictionaries

        Returns:
            List of invoice lines in Odoo format [(0, 0, values), ...]
        """
        prepared_lines = []

        for line in invoice_lines:
            line_values = {
                "product_id": line.get("product_id"),
                "name": line.get("name", ""),
                "quantity": line.get("quantity", 1.0),
                "price_unit": line.get("price_unit", 0.0),
            }

            # Add optional fields
            if "tax_ids" in line:
                line_values["tax_ids"] = [(6, 0, line["tax_ids"])]
            if "account_id" in line:
                line_values["account_id"] = line["account_id"]
            if "analytic_account_id" in line:
                line_values["analytic_account_id"] = line["analytic_account_id"]

            prepared_lines.append((0, 0, line_values))

        return prepared_lines

    def create_invoice_line(
        self,
        invoice_id: int,
        product_id: int,
        name: str,
        quantity: float,
        price_unit: float,
        tax_ids: list[int] | None = None,
        account_id: int | None = None,
        analytic_account_id: int | None = None,
    ) -> int:
        """
        Add a line to an existing invoice.

        Args:
            invoice_id: ID of the invoice
            product_id: ID of the product
            name: Description of the line
            quantity: Quantity
            price_unit: Unit price
            tax_ids: List of tax IDs
            account_id: Account ID
            analytic_account_id: Analytic account ID

        Returns:
            ID of the created invoice line
        """
        try:
            line_data = {
                "move_id": invoice_id,
                "product_id": product_id,
                "name": name,
                "quantity": quantity,
                "price_unit": price_unit,
            }

            if tax_ids:
                line_data["tax_ids"] = [(6, 0, tax_ids)]
            if account_id:
                line_data["account_id"] = account_id
            if analytic_account_id:
                line_data["analytic_account_id"] = analytic_account_id

            # Create invoice line using account.move.line model
            line_id = self.connection.create_record("account.move.line", line_data)

            logger.info(f"Created invoice line with ID: {line_id}")
            return line_id

        except Exception as e:
            logger.error(f"Failed to create invoice line: {e!s}")
            raise OdooResourceError(f"Failed to create invoice line: {e!s}")

    def get_invoice_lines(self, invoice_id: int) -> list[dict[str, Any]]:
        """
        Get all lines for an invoice.

        Args:
            invoice_id: ID of the invoice

        Returns:
            List of invoice line dictionaries
        """
        try:
            # Get invoice to find line IDs
            invoice = self.read(invoice_id, fields=["invoice_line_ids"])
            line_ids = invoice.get("invoice_line_ids", [])

            if not line_ids:
                return []

            # Read all invoice lines
            lines = self.connection.search_read(
                "account.move.line",
                [("id", "in", line_ids)],
                fields=[
                    "id",
                    "product_id",
                    "name",
                    "quantity",
                    "price_unit",
                    "price_subtotal",
                    "price_total",
                    "tax_ids",
                    "account_id",
                ],
            )

            return lines

        except Exception as e:
            logger.error(f"Failed to get invoice lines: {e!s}")
            raise OdooResourceError(f"Failed to get invoice lines: {e!s}")

    def validate_invoice(self, invoice_id: int) -> bool:
        """
        Validate an invoice (post it).

        Args:
            invoice_id: ID of the invoice to validate

        Returns:
            True if validation was successful
        """
        try:
            # Call the action_post method on the invoice
            result = self.connection.call_method(
                self.MODEL_NAME, "action_post", [invoice_id]
            )

            if result:
                logger.info(f"Validated invoice with ID: {invoice_id}")
            else:
                logger.warning(
                    f"Invoice validation returned False for ID: {invoice_id}"
                )

            return bool(result)

        except Exception as e:
            logger.error(f"Failed to validate invoice {invoice_id}: {e!s}")
            raise OdooResourceError(f"Failed to validate invoice: {e!s}")

    def cancel_invoice(self, invoice_id: int) -> bool:
        """
        Cancel an invoice.

        Args:
            invoice_id: ID of the invoice to cancel

        Returns:
            True if cancellation was successful
        """
        try:
            # Call the button_cancel method on the invoice
            result = self.connection.call_method(
                self.MODEL_NAME, "button_cancel", [invoice_id]
            )

            if result:
                logger.info(f"Cancelled invoice with ID: {invoice_id}")
            else:
                logger.warning(
                    f"Invoice cancellation returned False for ID: {invoice_id}"
                )

            return bool(result)

        except Exception as e:
            logger.error(f"Failed to cancel invoice {invoice_id}: {e!s}")
            raise OdooResourceError(f"Failed to cancel invoice: {e!s}")

    def get_invoice_amounts(self, invoice_id: int) -> dict[str, float]:
        """
        Get invoice amounts (untaxed, tax, total, residual).

        Args:
            invoice_id: ID of the invoice

        Returns:
            Dictionary with amount information
        """
        try:
            invoice = self.read(
                invoice_id,
                fields=[
                    "amount_untaxed",
                    "amount_tax",
                    "amount_total",
                    "amount_residual",
                ],
            )

            return {
                "untaxed": float(invoice.get("amount_untaxed", 0.0)),
                "tax": float(invoice.get("amount_tax", 0.0)),
                "total": float(invoice.get("amount_total", 0.0)),
                "residual": float(invoice.get("amount_residual", 0.0)),
            }

        except Exception as e:
            logger.error(f"Failed to get invoice amounts: {e!s}")
            raise OdooResourceError(f"Failed to get invoice amounts: {e!s}")

    def search_by_partner(
        self, partner_id: int, limit: int | None = None
    ) -> list[dict[str, Any]]:
        """
        Search for invoices by partner.

        Args:
            partner_id: ID of the partner
            limit: Maximum number of records to return

        Returns:
            List of invoice dictionaries
        """
        domain = [
            ("partner_id", "=", partner_id),
            ("move_type", "in", ["out_invoice", "in_invoice"]),
        ]

        return self.search(domain=domain, limit=limit)

    def search_by_date_range(
        self,
        start_date: datetime,
        end_date: datetime,
        move_type: str | None = None,
        limit: int | None = None,
    ) -> list[dict[str, Any]]:
        """
        Search for invoices by date range.

        Args:
            start_date: Start date
            end_date: End date
            move_type: Type of move (optional)
            limit: Maximum number of records to return

        Returns:
            List of invoice dictionaries
        """
        domain = [
            ("invoice_date", ">=", start_date.strftime("%Y-%m-%d")),
            ("invoice_date", "<=", end_date.strftime("%Y-%m-%d")),
            ("move_type", "in", ["out_invoice", "in_invoice"]),
        ]

        if move_type:
            domain = [("move_type", "=", move_type)] + domain[2:]

        return self.search(domain=domain, limit=limit)

    def search_draft_invoices(self, limit: int | None = None) -> list[dict[str, Any]]:
        """
        Search for draft invoices.

        Args:
            limit: Maximum number of records to return

        Returns:
            List of draft invoice dictionaries
        """
        domain = [
            ("state", "=", "draft"),
            ("move_type", "in", ["out_invoice", "in_invoice"]),
        ]

        return self.search(domain=domain, limit=limit)

    def search_paid_invoices(self, limit: int | None = None) -> list[dict[str, Any]]:
        """
        Search for paid invoices.

        Args:
            limit: Maximum number of records to return

        Returns:
            List of paid invoice dictionaries
        """
        domain = [
            ("state", "=", "posted"),
            ("payment_state", "=", "paid"),
            ("move_type", "in", ["out_invoice", "in_invoice"]),
        ]

        return self.search(domain=domain, limit=limit)

    def get_partner_invoices_summary(self, partner_id: int) -> dict[str, Any]:
        """
        Get a summary of invoices for a partner.

        Args:
            partner_id: ID of the partner

        Returns:
            Dictionary with invoice summary
        """
        try:
            invoices = self.search_by_partner(partner_id)

            total_amount = 0.0
            paid_amount = 0.0
            draft_count = 0
            posted_count = 0
            cancelled_count = 0

            for invoice in invoices:
                amount = float(invoice.get("amount_total", 0.0))
                state = invoice.get("state", "draft")

                total_amount += amount

                if state == "draft":
                    draft_count += 1
                elif state == "posted":
                    posted_count += 1
                    if invoice.get("payment_state") == "paid":
                        paid_amount += amount
                elif state == "cancelled":
                    cancelled_count += 1

            return {
                "total_invoices": len(invoices),
                "total_amount": total_amount,
                "paid_amount": paid_amount,
                "outstanding_amount": total_amount - paid_amount,
                "draft_count": draft_count,
                "posted_count": posted_count,
                "cancelled_count": cancelled_count,
            }

        except Exception as e:
            logger.error(f"Failed to get partner invoices summary: {e!s}")
            raise OdooResourceError(f"Failed to get partner invoices summary: {e!s}")

    def check_by_care_id(self, care_id: str) -> bool:
        """
        Check if an invoice exists in Odoo by Care ID.
        """
        return
