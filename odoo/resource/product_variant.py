import logging

from odoo.resource.base import OdooBaseResource

logger = logging.getLogger(__name__)


class OdooProductVariantResource(OdooBaseResource):
    resource_name = "product.product"

    def get_product_variant(self, product_id):
        return self.get_odoo_model().search([("product_tmpl_id", "=", product_id)])[0]
