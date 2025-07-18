from odoo.resource.base import OdooBaseResource


class OdooStateResource(OdooBaseResource):
    resource_name = "res.country.state"

    def get_state_id(self, state_code: str) -> int:
        model = self.get_odoo_model()
        results = model.search([("name", "=", state_code)], limit=1)
        return results[0]
