from odoo.connector.connector import OdooConnector


class OdooBaseResource:
    resource_name = None

    def get_odoo_model(self):
        return OdooConnector.get_model(self.resource_name)

    def find_by_care_id(self, care_id: str):
        """
        Find a partner by Care ID.
        """
        model = self.get_odoo_model()
        results = model.search([("x_care_id", "=", care_id)], limit=1)
        if results and len(results) != 0:
            return results[0]
        return None
