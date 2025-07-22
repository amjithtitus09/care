import logging
from decimal import Decimal

from care.emr.models.charge_item import ChargeItem
from care.emr.models.invoice import Invoice
from care.emr.resources.common.monetary_component import MonetaryComponentType
from odoo.connector.connector import OdooConnector
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

    def create_invoice(self, invoice, partner_id, invoice_line_ids) -> int:
        # Prepare invoice data
        from odoo.resource.currency import OdooCurrencyResource
        from odoo.resource.state import OdooStateResource

        invoice_data = {
            "name": invoice.number,
            "partner_id": partner_id,
            "invoice_date": invoice.created_date.strftime("%Y-%m-%d"),
            "move_type": "out_invoice",
            "x_care_id": str(invoice.external_id),
            "invoice_line_ids": invoice_line_ids,
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
        invoice = None  # self.find_by_care_id(str(invoice.external_id))
        if not invoice:
            invoice = self.get_odoo_model().create(invoice_data)

        logger.info(f"Created invoice with ID: {invoice}")
        return invoice

    def get_charge_item_base_price(self, charge_item: ChargeItem):
        for item in charge_item.unit_price_components:
            if item["monetary_component_type"] == MonetaryComponentType.base.value:
                return item["amount"]
        raise Exception("Base price not found")

    def get_taxes(self, charge_item: ChargeItem):
        from odoo.resource.tax import OdooTaxResource

        tax_items = []
        for item in charge_item.unit_price_components:
            if item["monetary_component_type"] == MonetaryComponentType.tax.value:
                item_code = item["code"]
                unique_id = (
                    f"{item_code['system']}/{item_code['code']}/{item['factor']!s} "
                )
                tax_item = OdooTaxResource().get_or_create_tax_item(unique_id, item)
                tax_items.append(tax_item)
        return tax_items

    def get_discounts(
        self, charge_item: ChargeItem, unit_price: float, quantity: Decimal
    ):
        from odoo.resource.product import OdooProductResource

        discount_items = []
        for item in charge_item.unit_price_components:
            if item["monetary_component_type"] == MonetaryComponentType.discount.value:
                discount_amount = (
                    (Decimal(item["factor"]) / Decimal(100))
                    * Decimal(unit_price)
                    * quantity
                )
                # Get product id
                discount_unique_slug = (
                    f"{item['code']['system']}/{item['code']['code']}"
                )
                discount_product_id = (
                    OdooProductResource().get_or_create_discount_product(
                        discount_unique_slug, item["code"]["display"]
                    )
                )
                discount_items.append(
                    {"amount": discount_amount, "product_id": discount_product_id}
                )
        return discount_items

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

    def post_invoice(self, invoice_id: str):
        OdooConnector.get_connection().execute(
            "account.move", "action_post", [invoice_id]
        )

    def sync_invoice_to_odoo(self, invoice_id: str) -> int | None:
        """
        Synchronize a Django invoice to Odoo.

        Args:
            invoice_id: External ID of the Django invoice

        Returns:
            Odoo invoice ID if successful, None otherwise
        """
        from odoo.resource.partner import OdooPartnerResource
        from odoo.resource.product import OdooProductResource

        # Get the Django invoice
        invoice = Invoice.objects.select_related("facility", "patient", "account").get(
            external_id=invoice_id
        )

        partner = OdooPartnerResource().get_or_create_patient_partner(invoice.patient)

        # Create Products for each charge item Def
        mapping = {}
        for charge_item in ChargeItem.objects.filter(
            paid_invoice=invoice
        ).select_related("charge_item_definition"):
            if charge_item.charge_item_definition:
                logging.info(charge_item.charge_item_definition)
                product_id = OdooProductResource().get_or_create_patient_partner(
                    charge_item.charge_item_definition
                )
                mapping[charge_item.charge_item_definition.external_id] = product_id
        # Create line items for each charge item
        line_id = 100
        line_items = []
        for charge_item in ChargeItem.objects.filter(
            paid_invoice=invoice
        ).select_related("charge_item_definition"):
            unit_price = self.get_charge_item_base_price(charge_item)
            taxes = self.get_taxes(charge_item)
            discounts = self.get_discounts(
                charge_item, unit_price, charge_item.quantity
            )
            line_item = {
                "sequence": line_id,
                "product_id": mapping.get(
                    charge_item.charge_item_definition.external_id
                )
                if charge_item.charge_item_definition
                else None,
                # "name": charge_item.title,
                "tax_ids": taxes,
                "quantity": str(charge_item.quantity),
                "price_unit": unit_price,
            }
            line_items.append([0, f"{line_id}", line_item])
            if discounts:
                for discount in discounts:
                    line_id += 1
                    line_item = line_item.copy()
                    line_item["sequence"] = line_id
                    line_item["product_id"] = discount["product_id"]
                    line_item["price_unit"] = str(-1 * discount["amount"])
                    line_items.append([0, f"{line_id}", line_item])
            line_id += 1
        logging.info(line_items)
        # Create invoice in Odoo
        odoo_invoice_id = self.create_invoice(invoice, partner, line_items)
        self.post_invoice(odoo_invoice_id)
        logger.info(
            f"Successfully synced invoice {invoice_id} to Odoo with ID: {odoo_invoice_id}"
        )
        return odoo_invoice_id
