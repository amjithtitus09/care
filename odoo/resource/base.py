from odoo.connector.connector import OdooConnector


class OdooBaseResource:
    resource_name = None

    def get_odoo_model(self):
        return OdooConnector.get_model(self.resource_name)
