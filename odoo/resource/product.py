import logging
from typing import Any

from odoo.resource.base import OdooResource, OdooResourceError

logger = logging.getLogger(__name__)


class OdooProductResource(OdooResource):
    """
    Odoo resource for handling product operations (product.product model).
    This class provides methods to create, read, update, and delete products
    and services in Odoo.
    """

    MODEL_NAME = "product.product"

    # Fields for creating products
    CREATE_FIELDS = [
        "name",
        "type",
        "categ_id",
        "list_price",
        "standard_price",
        "default_code",
        "barcode",
        "description",
        "description_sale",
        "description_purchase",
        "uom_id",
        "uom_po_id",
        "tracking",
        "sale_ok",
        "purchase_ok",
        "can_be_expensed",
        "taxes_id",
        "supplier_taxes_id",
    ]

    # Fields for updating products
    UPDATE_FIELDS = [
        "name",
        "list_price",
        "standard_price",
        "default_code",
        "barcode",
        "description",
        "description_sale",
        "description_purchase",
        "sale_ok",
        "purchase_ok",
        "can_be_expensed",
        "taxes_id",
        "supplier_taxes_id",
    ]

    # Fields for reading products
    READ_FIELDS = [
        "id",
        "name",
        "type",
        "categ_id",
        "list_price",
        "standard_price",
        "default_code",
        "barcode",
        "description",
        "description_sale",
        "description_purchase",
        "uom_id",
        "uom_po_id",
        "tracking",
        "sale_ok",
        "purchase_ok",
        "can_be_expensed",
        "taxes_id",
        "supplier_taxes_id",
        "create_date",
        "write_date",
    ]

    # Default search domain for products
    DEFAULT_DOMAIN = [("active", "=", True)]

    # Default ordering
    DEFAULT_ORDER = "name asc"

    def create_service(
        self,
        name: str,
        list_price: float = 0.0,
        standard_price: float = 0.0,
        default_code: str | None = None,
        description: str | None = None,
        description_sale: str | None = None,
        description_purchase: str | None = None,
        categ_id: int = 1,  # Default category
        sale_ok: bool = True,
        purchase_ok: bool = False,
        can_be_expensed: bool = False,
        taxes_id: list[int] | None = None,
        supplier_taxes_id: list[int] | None = None,
    ) -> int:
        """
        Create a new service in Odoo.

        Args:
            name: Product name
            list_price: Sale price
            standard_price: Cost price
            default_code: Internal reference
            description: Description
            description_sale: Sales description
            description_purchase: Purchase description
            categ_id: Product category ID
            sale_ok: Can be sold
            purchase_ok: Can be purchased
            can_be_expensed: Can be expensed
            taxes_id: Customer taxes
            supplier_taxes_id: Supplier taxes

        Returns:
            ID of the created product
        """
        product_data = {
            "name": name,
            "type": "service",
            "categ_id": categ_id,
            "list_price": list_price,
            "standard_price": standard_price,
            "sale_ok": sale_ok,
            "purchase_ok": purchase_ok,
            "can_be_expensed": can_be_expensed,
        }

        # Add optional fields
        if default_code:
            product_data["default_code"] = default_code
        if description:
            product_data["description"] = description
        if description_sale:
            product_data["description_sale"] = description_sale
        if description_purchase:
            product_data["description_purchase"] = description_purchase
        if taxes_id:
            product_data["taxes_id"] = [(6, 0, taxes_id)]
        if supplier_taxes_id:
            product_data["supplier_taxes_id"] = [(6, 0, supplier_taxes_id)]

        return self.create(product_data)

    def create_consumable(
        self,
        name: str,
        list_price: float = 0.0,
        standard_price: float = 0.0,
        default_code: str | None = None,
        barcode: str | None = None,
        description: str | None = None,
        description_sale: str | None = None,
        description_purchase: str | None = None,
        categ_id: int = 1,  # Default category
        uom_id: int = 1,  # Default UoM
        tracking: str = "none",  # none, serial, lot
        sale_ok: bool = True,
        purchase_ok: bool = True,
        taxes_id: list[int] | None = None,
        supplier_taxes_id: list[int] | None = None,
    ) -> int:
        """
        Create a new consumable product in Odoo.

        Args:
            name: Product name
            list_price: Sale price
            standard_price: Cost price
            default_code: Internal reference
            barcode: Barcode
            description: Description
            description_sale: Sales description
            description_purchase: Purchase description
            categ_id: Product category ID
            uom_id: Unit of measure ID
            tracking: Tracking type (none, serial, lot)
            sale_ok: Can be sold
            purchase_ok: Can be purchased
            taxes_id: Customer taxes
            supplier_taxes_id: Supplier taxes

        Returns:
            ID of the created product
        """
        product_data = {
            "name": name,
            "type": "consu",
            "categ_id": categ_id,
            "list_price": list_price,
            "standard_price": standard_price,
            "uom_id": uom_id,
            "tracking": tracking,
            "sale_ok": sale_ok,
            "purchase_ok": purchase_ok,
        }

        # Add optional fields
        if default_code:
            product_data["default_code"] = default_code
        if barcode:
            product_data["barcode"] = barcode
        if description:
            product_data["description"] = description
        if description_sale:
            product_data["description_sale"] = description_sale
        if description_purchase:
            product_data["description_purchase"] = description_purchase
        if taxes_id:
            product_data["taxes_id"] = [(6, 0, taxes_id)]
        if supplier_taxes_id:
            product_data["supplier_taxes_id"] = [(6, 0, supplier_taxes_id)]

        return self.create(product_data)

    def create_storable(
        self,
        name: str,
        list_price: float = 0.0,
        standard_price: float = 0.0,
        default_code: str | None = None,
        barcode: str | None = None,
        description: str | None = None,
        description_sale: str | None = None,
        description_purchase: str | None = None,
        categ_id: int = 1,  # Default category
        uom_id: int = 1,  # Default UoM
        uom_po_id: int = 1,  # Default purchase UoM
        tracking: str = "lot",  # none, serial, lot
        sale_ok: bool = True,
        purchase_ok: bool = True,
        taxes_id: list[int] | None = None,
        supplier_taxes_id: list[int] | None = None,
    ) -> int:
        """
        Create a new storable product in Odoo.

        Args:
            name: Product name
            list_price: Sale price
            standard_price: Cost price
            default_code: Internal reference
            barcode: Barcode
            description: Description
            description_sale: Sales description
            description_purchase: Purchase description
            categ_id: Product category ID
            uom_id: Unit of measure ID
            uom_po_id: Purchase unit of measure ID
            tracking: Tracking type (none, serial, lot)
            sale_ok: Can be sold
            purchase_ok: Can be purchased
            taxes_id: Customer taxes
            supplier_taxes_id: Supplier taxes

        Returns:
            ID of the created product
        """
        product_data = {
            "name": name,
            "type": "product",
            "categ_id": categ_id,
            "list_price": list_price,
            "standard_price": standard_price,
            "uom_id": uom_id,
            "uom_po_id": uom_po_id,
            "tracking": tracking,
            "sale_ok": sale_ok,
            "purchase_ok": purchase_ok,
        }

        # Add optional fields
        if default_code:
            product_data["default_code"] = default_code
        if barcode:
            product_data["barcode"] = barcode
        if description:
            product_data["description"] = description
        if description_sale:
            product_data["description_sale"] = description_sale
        if description_purchase:
            product_data["description_purchase"] = description_purchase
        if taxes_id:
            product_data["taxes_id"] = [(6, 0, taxes_id)]
        if supplier_taxes_id:
            product_data["supplier_taxes_id"] = [(6, 0, supplier_taxes_id)]

        return self.create(product_data)

    def search_by_name(
        self, name: str, limit: int | None = None
    ) -> list[dict[str, Any]]:
        """
        Search for products by name.

        Args:
            name: Product name (partial match)
            limit: Maximum number of records to return

        Returns:
            List of product dictionaries
        """
        domain = [("name", "ilike", name), ("active", "=", True)]
        return self.search(domain=domain, limit=limit)

    def search_by_code(
        self, code: str, limit: int | None = None
    ) -> list[dict[str, Any]]:
        """
        Search for products by internal reference code.

        Args:
            code: Internal reference code
            limit: Maximum number of records to return

        Returns:
            List of product dictionaries
        """
        domain = [("default_code", "ilike", code), ("active", "=", True)]
        return self.search(domain=domain, limit=limit)

    def search_by_barcode(
        self, barcode: str, limit: int | None = None
    ) -> list[dict[str, Any]]:
        """
        Search for products by barcode.

        Args:
            barcode: Barcode
            limit: Maximum number of records to return

        Returns:
            List of product dictionaries
        """
        domain = [("barcode", "=", barcode), ("active", "=", True)]
        return self.search(domain=domain, limit=limit)

    def search_services(self, limit: int | None = None) -> list[dict[str, Any]]:
        """
        Search for service products.

        Args:
            limit: Maximum number of records to return

        Returns:
            List of service product dictionaries
        """
        domain = [("type", "=", "service"), ("active", "=", True)]
        return self.search(domain=domain, limit=limit)

    def search_consumables(self, limit: int | None = None) -> list[dict[str, Any]]:
        """
        Search for consumable products.

        Args:
            limit: Maximum number of records to return

        Returns:
            List of consumable product dictionaries
        """
        domain = [("type", "=", "consu"), ("active", "=", True)]
        return self.search(domain=domain, limit=limit)

    def search_storables(self, limit: int | None = None) -> list[dict[str, Any]]:
        """
        Search for storable products.

        Args:
            limit: Maximum number of records to return

        Returns:
            List of storable product dictionaries
        """
        domain = [("type", "=", "product"), ("active", "=", True)]
        return self.search(domain=domain, limit=limit)

    def get_product_by_code(self, code: str) -> dict[str, Any] | None:
        """
        Get product by internal reference code.

        Args:
            code: Internal reference code

        Returns:
            Product dictionary if found, None otherwise
        """
        products = self.search_by_code(code, limit=1)
        return products[0] if products else None

    def get_product_by_barcode(self, barcode: str) -> dict[str, Any] | None:
        """
        Get product by barcode.

        Args:
            barcode: Barcode

        Returns:
            Product dictionary if found, None otherwise
        """
        products = self.search_by_barcode(barcode, limit=1)
        return products[0] if products else None

    def update_prices(
        self,
        product_id: int,
        list_price: float | None = None,
        standard_price: float | None = None,
    ) -> bool:
        """
        Update product prices.

        Args:
            product_id: ID of the product
            list_price: New sale price
            standard_price: New cost price

        Returns:
            True if update was successful
        """
        update_data = {}

        if list_price is not None:
            update_data["list_price"] = list_price
        if standard_price is not None:
            update_data["standard_price"] = standard_price

        if update_data:
            return self.update(product_id, update_data)

        return True

    def get_product_stock(self, product_id: int) -> dict[str, Any]:
        """
        Get product stock information.

        Args:
            product_id: ID of the product

        Returns:
            Dictionary with stock information
        """
        try:
            # Get product with stock fields
            product = self.read(
                product_id,
                fields=[
                    "id",
                    "name",
                    "type",
                    "qty_available",
                    "virtual_available",
                    "incoming_qty",
                    "outgoing_qty",
                    "location_id",
                ],
            )

            return {
                "product_id": product.get("id"),
                "name": product.get("name"),
                "type": product.get("type"),
                "qty_available": float(product.get("qty_available", 0.0)),
                "virtual_available": float(product.get("virtual_available", 0.0)),
                "incoming_qty": float(product.get("incoming_qty", 0.0)),
                "outgoing_qty": float(product.get("outgoing_qty", 0.0)),
            }

        except Exception as e:
            logger.error(f"Failed to get product stock: {e!s}")
            raise OdooResourceError(f"Failed to get product stock: {e!s}")

    def get_product_categories(self) -> list[dict[str, Any]]:
        """
        Get all product categories.

        Returns:
            List of product category dictionaries
        """
        try:
            categories = self.connection.search_read(
                "product.category",
                [("active", "=", True)],
                fields=["id", "name", "parent_id", "complete_name"],
                order="name asc",
            )
            return categories

        except Exception as e:
            logger.error(f"Failed to get product categories: {e!s}")
            raise OdooResourceError(f"Failed to get product categories: {e!s}")

    def get_units_of_measure(self) -> list[dict[str, Any]]:
        """
        Get all units of measure.

        Returns:
            List of unit of measure dictionaries
        """
        try:
            uoms = self.connection.search_read(
                "uom.uom",
                [("active", "=", True)],
                fields=["id", "name", "category_id", "uom_type"],
                order="name asc",
            )
            return uoms

        except Exception as e:
            logger.error(f"Failed to get units of measure: {e!s}")
            raise OdooResourceError(f"Failed to get units of measure: {e!s}")
