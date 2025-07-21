import logging

from odoo.resource.base import OdooBaseResource

logger = logging.getLogger(__name__)


class OdooTaxResource(OdooBaseResource):
    resource_name = "account.tax"

    def create_tax_item(
        self,
        data: dict,
    ) -> int:
        tax_data = {
            "x_care_id": data.pop("care_id"),
            **data,
        }

        return self.get_odoo_model().create(tax_data)

    def get_or_create_tax_item(self, unique_slug, data) -> int:
        from odoo.resource.tax_group import OdooTaxGroupResource

        tax_name = f"CARE : {unique_slug}"
        tax_group_id = OdooTaxGroupResource().get_tax_group_id(data["code"]["code"])

        existing_tax_id = self.find_by_care_id(unique_slug)
        if not existing_tax_id:
            data = {
                "name": tax_name,
                "amount_type": "percent",
                # "formula": "price_unit * 0.10",
                "type_tax_use": "sale",
                "amount": data["factor"],
                "invoice_repartition_line_ids": [
                    [
                        0,
                        "virtual_19",
                        {
                            "sequence": 1,
                            "factor_percent": 100,
                            "repartition_type": "base",
                            "account_id": False,
                            "tag_ids": [],
                            "use_in_tax_closing": False,
                        },
                    ],
                    [
                        0,
                        "virtual_22",
                        {
                            "sequence": 1,
                            "factor_percent": 100,
                            "repartition_type": "tax",
                            "account_id": False,
                            "tag_ids": [],
                            "use_in_tax_closing": False,
                        },
                    ],
                ],
                "invoice_label": "5%",
                "tax_group_id": tax_group_id,
                "country_id": 104,
                "care_id": unique_slug,
            }
            existing_tax_id = self.create_tax_item(data=data)
        return existing_tax_id
