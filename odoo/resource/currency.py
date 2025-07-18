from odoo.resource.base import OdooBaseResource


class OdooCurrencyResource(OdooBaseResource):
    resource_name = "res.currency"

    def get_currency_id(self, currency_code: str) -> int:
        model = self.get_odoo_model()
        results = model.search([("name", "=", currency_code)], limit=1)
        return results[0]
