import logging
from typing import Any

from odoo.resource.base import OdooResource, OdooResourceError

logger = logging.getLogger(__name__)


class OdooPartnerResource(OdooResource):
    """
    Odoo resource for handling partner operations (res.partner model).
    This class provides methods to create, read, update, and delete partners
    (customers and vendors) in Odoo.
    """

    MODEL_NAME = "res.partner"

    # Fields for creating partners
    CREATE_FIELDS = [
        "name",
        "is_company",
        "customer_rank",
        "supplier_rank",
        "email",
        "phone",
        "mobile",
        "street",
        "street2",
        "city",
        "state_id",
        "zip",
        "country_id",
        "vat",
        "ref",
        "comment",
        "category_id",
        "x_care_id",
    ]

    # Fields for updating partners
    UPDATE_FIELDS = [
        "name",
        "email",
        "phone",
        "mobile",
        "street",
        "street2",
        "city",
        "state_id",
        "zip",
        "country_id",
        "vat",
        "ref",
        "comment",
        "category_id",
    ]

    # Fields for reading partners
    READ_FIELDS = [
        "id",
        "name",
        "is_company",
        "customer_rank",
        "supplier_rank",
        "email",
        "phone",
        "mobile",
        "street",
        "street2",
        "city",
        "state_id",
        "zip",
        "country_id",
        "vat",
        "ref",
        "comment",
        "category_id",
        "create_date",
        "write_date",
    ]

    # Default search domain for partners
    DEFAULT_DOMAIN = []

    # Default ordering
    DEFAULT_ORDER = "name asc"

    def create_customer(
        self,
        name: str,
        care_id: str,
        email: str | None = None,
        phone: str | None = None,
        mobile: str | None = None,
        street: str | None = None,
        street2: str | None = None,
        city: str | None = None,
        state_id: int | None = None,
        country_id: int | None = None,
        zip: str | None = None,
        vat: str | None = None,
        ref: str | None = None,
        comment: str | None = None,
        is_company: bool = False,
    ) -> int:
        """
        Create a new customer in Odoo.

        Args:
            name: Partner name
            email: Email address
            phone: Phone number
            mobile: Mobile number
            street: Street address
            city: City
            state_id: State/Province ID
            country_id: Country ID
            vat: VAT number
            ref: Reference number
            comment: Additional notes
            is_company: Whether this is a company

        Returns:
            ID of the created partner
        """
        partner_data = {
            "name": name,
            "is_company": is_company,
            "customer_rank": 1,  # Mark as customer
            "supplier_rank": 0,
            "x_care_id": care_id,
        }

        # Add optional fields
        partner_data["email"] = email if email else ""
        partner_data["phone"] = phone if phone else ""
        partner_data["mobile"] = mobile if mobile else ""
        partner_data["street"] = street if street else ""
        partner_data["street2"] = street2 if street2 else ""
        partner_data["zip"] = zip if zip else ""
        partner_data["category_id"] = None
        partner_data["city"] = city if city else ""
        partner_data["state_id"] = state_id if state_id else ""
        partner_data["country_id"] = country_id if country_id else ""
        partner_data["vat"] = vat if vat else ""
        partner_data["ref"] = ref if ref else ""
        partner_data["comment"] = comment if comment else ""

        return self.create(partner_data)

    def create_supplier(
        self,
        name: str,
        email: str | None = None,
        phone: str | None = None,
        mobile: str | None = None,
        street: str | None = None,
        city: str | None = None,
        state_id: int | None = None,
        country_id: int | None = None,
        vat: str | None = None,
        ref: str | None = None,
        comment: str | None = None,
        is_company: bool = True,
    ) -> int:
        """
        Create a new supplier in Odoo.

        Args:
            name: Partner name
            email: Email address
            phone: Phone number
            mobile: Mobile number
            street: Street address
            city: City
            state_id: State/Province ID
            country_id: Country ID
            vat: VAT number
            ref: Reference number
            comment: Additional notes
            is_company: Whether this is a company

        Returns:
            ID of the created partner
        """
        partner_data = {
            "name": name,
            "is_company": is_company,
            "customer_rank": 0,
            "supplier_rank": 1,  # Mark as supplier
        }

        # Add optional fields
        if email:
            partner_data["email"] = email
        if phone:
            partner_data["phone"] = phone
        if mobile:
            partner_data["mobile"] = mobile
        if street:
            partner_data["street"] = street
        if city:
            partner_data["city"] = city
        if state_id:
            partner_data["state_id"] = state_id
        if country_id:
            partner_data["country_id"] = country_id
        if vat:
            partner_data["vat"] = vat
        if ref:
            partner_data["ref"] = ref
        if comment:
            partner_data["comment"] = comment

        return self.create(partner_data)

    def search_customers(
        self,
        name: str | None = None,
        email: str | None = None,
        limit: int | None = None,
    ) -> list[dict[str, Any]]:
        """
        Search for customers.

        Args:
            name: Partner name (partial match)
            email: Email address (exact match)
            limit: Maximum number of records to return

        Returns:
            List of customer dictionaries
        """
        domain = [("customer_rank", ">", 0)]

        if name:
            domain.append(("name", "ilike", name))
        if email:
            domain.append(("email", "=", email))

        return self.search(domain=domain, limit=limit)

    def search_suppliers(
        self,
        name: str | None = None,
        email: str | None = None,
        limit: int | None = None,
    ) -> list[dict[str, Any]]:
        """
        Search for suppliers.

        Args:
            name: Partner name (partial match)
            email: Email address (exact match)
            limit: Maximum number of records to return

        Returns:
            List of supplier dictionaries
        """
        domain = [("supplier_rank", ">", 0)]

        if name:
            domain.append(("name", "ilike", name))
        if email:
            domain.append(("email", "=", email))

        return self.search(domain=domain, limit=limit)

    def get_partner_by_email(self, email: str) -> dict[str, Any] | None:
        """
        Get partner by email address.

        Args:
            email: Email address

        Returns:
            Partner dictionary if found, None otherwise
        """
        partners = self.search(domain=[("email", "=", email)], limit=1)
        return partners[0] if partners else None

    def get_partner_by_name(self, name: str) -> dict[str, Any] | None:
        """
        Get partner by name.

        Args:
            name: Partner name

        Returns:
            Partner dictionary if found, None otherwise
        """
        partners = self.search(domain=[("name", "=", name)], limit=1)
        return partners[0] if partners else None

    def update_partner_rank(
        self,
        partner_id: int,
        customer_rank: int | None = None,
        supplier_rank: int | None = None,
    ) -> bool:
        """
        Update partner customer/supplier rank.

        Args:
            partner_id: ID of the partner
            customer_rank: Customer rank (0 to disable, >0 to enable)
            supplier_rank: Supplier rank (0 to disable, >0 to enable)

        Returns:
            True if update was successful
        """
        update_data = {}

        if customer_rank is not None:
            update_data["customer_rank"] = customer_rank
        if supplier_rank is not None:
            update_data["supplier_rank"] = supplier_rank

        if update_data:
            return self.update(partner_id, update_data)

        return True

    def get_partner_invoices(
        self, partner_id: int, limit: int | None = None
    ) -> list[dict[str, Any]]:
        """
        Get all invoices for a partner.

        Args:
            partner_id: ID of the partner
            limit: Maximum number of records to return

        Returns:
            List of invoice dictionaries
        """
        try:
            invoices = self.connection.search_read(
                "account.move",
                [("partner_id", "=", partner_id)],
                fields=[
                    "id",
                    "name",
                    "invoice_date",
                    "amount_total",
                    "state",
                    "move_type",
                    "ref",
                    "payment_state",
                ],
                limit=limit,
            )
            return invoices

        except Exception as e:
            logger.error(f"Failed to get partner invoices: {e!s}")
            raise OdooResourceError(f"Failed to get partner invoices: {e!s}")

    def get_partner_summary(self, partner_id: int) -> dict[str, Any]:
        """
        Get a summary of partner information including invoices.

        Args:
            partner_id: ID of the partner

        Returns:
            Dictionary with partner summary
        """
        try:
            partner = self.read(partner_id)
            invoices = self.get_partner_invoices(partner_id)

            total_invoices = len(invoices)
            total_amount = sum(float(inv.get("amount_total", 0.0)) for inv in invoices)
            paid_amount = sum(
                float(inv.get("amount_total", 0.0))
                for inv in invoices
                if inv.get("payment_state") == "paid"
            )

            return {
                "partner": partner,
                "total_invoices": total_invoices,
                "total_amount": total_amount,
                "paid_amount": paid_amount,
                "outstanding_amount": total_amount - paid_amount,
                "recent_invoices": invoices[:5],  # Last 5 invoices
            }

        except Exception as e:
            logger.error(f"Failed to get partner summary: {e!s}")
            raise OdooResourceError(f"Failed to get partner summary: {e!s}")

    def find_by_care_id(self, care_id: str) -> dict[str, Any] | None:
        """
        Find a partner by Care ID.
        """
        results = self.search(domain=[("x_care_id", "=", care_id)], limit=1)
        if results and len(results) != 0:
            return results[0]
        return None

    def get_or_create_patient_partner(self, patient) -> int:
        patient_name = f"CARE : {patient.name}"
        patient_id = str(patient.external_id)
        existing_parter = self.find_by_care_id(patient_id)
        if not existing_parter:
            self.create_customer(
                name=patient_name, phone=patient.phone_number, care_id=patient_id
            )
        return {}
