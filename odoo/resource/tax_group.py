from odoo.resource.base import OdooBaseResource


class OdooTaxGroupResource(OdooBaseResource):
    resource_name = "account.tax.group"

    def get_tax_group_id(self, tax_group_name: str) -> int:
        model = self.get_odoo_model()
        results = model.search([("name", "=", tax_group_name.upper())], limit=1)
        return results[0]
