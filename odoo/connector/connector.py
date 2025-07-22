import odoorpc
from django.conf import settings


class OdooConnector:
    connection = None
    is_authenticated = False

    @classmethod
    def get_connection(cls):
        if not cls.connection:
            cls.connection = odoorpc.ODOO(
                settings.ODOO_CONFIG["host"],
                port=settings.ODOO_CONFIG["port"],
                protocol=settings.ODOO_CONFIG["protocol"],
            )
            cls.connection.login(
                settings.ODOO_CONFIG["database"],
                settings.ODOO_CONFIG["username"],
                settings.ODOO_CONFIG["password"],
            )
            cls.validate_connection()
        return cls.connection

    @classmethod
    def validate_connection(cls):
        if not cls.connection.env.user:
            cls.is_authenticated = False
        else:
            cls.is_authenticated = True

    @classmethod
    def get_model(cls, model_name: str):
        cls.get_connection()
        return cls.connection.env[model_name]
