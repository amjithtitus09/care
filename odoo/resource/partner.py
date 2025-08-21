import logging
from typing import Any

from odoo.resource.base import OdooBaseResource

logger = logging.getLogger(__name__)


class OdooPartnerResource(OdooBaseResource):
    resource_name = "res.partner"

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
        zip_code: str | None = None,
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
        partner_data["zip"] = zip_code if zip_code else ""
        partner_data["category_id"] = None
        partner_data["city"] = city if city else ""
        partner_data["state_id"] = state_id if state_id else ""
        partner_data["country_id"] = country_id if country_id else ""
        partner_data["vat"] = vat if vat else ""
        partner_data["ref"] = ref if ref else ""
        partner_data["comment"] = comment if comment else ""
        return self.get_odoo_model().create(partner_data)

    def find_by_care_id(self, care_id: str) -> dict[str, Any] | None:
        """
        Find a partner by Care ID.
        """
        model = self.get_odoo_model()
        results = model.search([("x_care_id", "=", care_id)], limit=1)
        if results and len(results) != 0:
            return results[0]
        return None

    def get_or_create_patient_partner(self, patient) -> int:
        patient_name = f"CARE : {patient.name}"
        patient_id = str(patient.external_id)
        existing_partner_id = self.find_by_care_id(patient_id)
        if not existing_partner_id:
            existing_partner_id = self.create_customer(
                name=patient_name, phone=patient.phone_number, care_id=patient_id
            )
        return existing_partner_id
