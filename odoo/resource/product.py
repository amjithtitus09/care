import logging

from odoo.resource.base import OdooBaseResource

logger = logging.getLogger(__name__)


class OdooProductResource(OdooBaseResource):
    resource_name = "product.template"

    def create_product(
        self,
        data: dict,
    ) -> int:
        partner_data = {
            "x_care_id": data.pop("care_id"),
            **data,
        }

        return self.get_odoo_model().create(partner_data)

    def get_or_create_discount_product(self, unique_slug: str, name: str) -> int:
        existing_product_id = self.find_by_care_id(unique_slug)
        if not existing_product_id:
            existing_product_id = self.create_product(
                data={
                    "name": name,
                    "care_id": unique_slug,
                }
            )
        return existing_product_id

    def get_or_create_patient_partner(self, charge_item_definition) -> int:
        from odoo.resource.product_variant import OdooProductVariantResource

        product_name = f"CARE : {charge_item_definition.title}"
        product_id = str(charge_item_definition.external_id)
        existing_product_id = self.find_by_care_id(product_id)
        if not existing_product_id:
            existing_product_id = self.create_product(
                data={
                    "name": product_name,
                    "care_id": product_id,
                }
            )
        product_variant_id = OdooProductVariantResource().get_product_variant(
            existing_product_id
        )
        return product_variant_id
