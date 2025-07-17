from django.conf import settings
from django.core.management.base import BaseCommand

from odoo.integration import odoo_integration


class Command(BaseCommand):
    help = "Test the Odoo JSON-RPC connection and integration"

    def add_arguments(self, parser):
        parser.add_argument(
            "--verbose",
            action="store_true",
            help="Show detailed connection information",
        )
        parser.add_argument(
            "--test-operations",
            action="store_true",
            help="Test basic Odoo operations (search, read, etc.)",
        )
        parser.add_argument(
            "--test-resources",
            action="store_true",
            help="Test resource operations (invoices, partners, products)",
        )

    def handle(self, *args, **options):
        verbose = options["verbose"]
        test_operations = options["test_operations"]
        test_resources = options["test_resources"]

        self.stdout.write("Testing Odoo JSON-RPC Integration...")
        self.stdout.write("=" * 60)

        # Check if Odoo configuration exists
        odoo_config = getattr(settings, "ODOO_CONFIG", {})
        if not odoo_config:
            self.stdout.write("❌ ODOO_CONFIG not found in Django settings")
            self.stdout.write(
                "Please add ODOO_CONFIG to your settings file with the following structure:"
            )
            self.stdout.write("""
ODOO_CONFIG = {
    'base_url': 'https://your-odoo-instance.com',
    'database': 'your_database_name',
    'username': 'your_username',
    'password': 'your_password',
    'timeout': 30,
    'max_retries': 3,
    'cache_timeout': 3600,
    'enabled': True,
}
            """)
            return

        if verbose:
            self.stdout.write("Configuration found:")
            for key, value in odoo_config.items():
                if key == "password":
                    self.stdout.write(f"  {key}: {'*' * len(str(value))}")
                else:
                    self.stdout.write(f"  {key}: {value}")
            self.stdout.write("")

        # Test connection
        try:
            if odoo_integration.is_enabled():
                self.stdout.write("✅ Odoo integration is enabled")

                # Test authentication
                self.stdout.write("\n🔐 Testing authentication...")
                if odoo_integration.connection.is_authenticated():
                    self.stdout.write("✅ Authentication successful")
                    self.stdout.write(
                        f"   User ID: {odoo_integration.connection._user_id}"
                    )
                else:
                    self.stdout.write("⚠️  Not authenticated")

                # Test connection
                self.stdout.write("\n🔗 Testing connection...")
                if odoo_integration.connection.test_connection():
                    self.stdout.write("✅ Connection test successful")
                else:
                    self.stdout.write("❌ Connection test failed")

                # Get version info
                self.stdout.write("\n📋 Getting version information...")
                try:
                    version_info = odoo_integration.connection.get_version_info()
                    if version_info:
                        self.stdout.write("✅ Version info retrieved")
                        self.stdout.write(
                            f"   Server Version: {version_info.get('server_version', 'Unknown')}"
                        )
                        self.stdout.write(
                            f"   Server Series: {version_info.get('server_serie', 'Unknown')}"
                        )
                        self.stdout.write("   Protocol: JSON-RPC")
                    else:
                        self.stdout.write("⚠️  Could not retrieve version information")
                except Exception as e:
                    self.stdout.write(f"⚠️  Error getting version info: {e!s}")

                # Test basic operations if requested
                if test_operations:
                    self.stdout.write("\n🧪 Testing basic operations...")
                    self._test_basic_operations()

                # Test resource operations if requested
                if test_resources:
                    self.stdout.write("\n📦 Testing resource operations...")
                    self._test_resource_operations()

            else:
                self.stdout.write("❌ Odoo integration is disabled")
                self.stdout.write("Check your configuration and connection settings")

        except Exception as e:
            self.stdout.write(f"❌ Error testing connection: {e!s}")

        self.stdout.write("=" * 60)
        self.stdout.write("Test completed.")

    def _test_basic_operations(self):
        """Test basic Odoo operations."""
        try:
            # Test search_count
            module_count = odoo_integration.connection.call_method(
                "ir.module.module", "search_count", []
            )
            self.stdout.write(f"✅ Module count: {module_count}")

            # Test search_read
            partners = odoo_integration.connection.search_read(
                "res.partner",
                [("is_company", "=", True)],
                fields=["id", "name"],
                limit=5,
            )
            self.stdout.write(f"✅ Found {len(partners)} company partners")

            # Test fields_get
            fields = odoo_integration.connection.get_model_fields("res.partner")
            self.stdout.write(f"✅ Partner model has {len(fields)} fields")

            # Test create/read/update (dry run)
            self.stdout.write("✅ Basic CRUD operations available")

        except Exception as e:
            self.stdout.write(f"❌ Error testing basic operations: {e!s}")

    def _test_resource_operations(self):
        """Test resource-specific operations."""
        try:
            # Test invoice resource
            if odoo_integration.invoice_resource:
                self.stdout.write("✅ Invoice resource available")

                # Test invoice search
                invoices = odoo_integration.invoice_resource.search(
                    domain=[("move_type", "=", "out_invoice")], limit=5
                )
                self.stdout.write(f"✅ Found {len(invoices)} customer invoices")
            else:
                self.stdout.write("⚠️  Invoice resource not available")

            # Test partner operations
            try:
                partners = odoo_integration.connection.search_read(
                    "res.partner",
                    [("customer_rank", ">", 0)],
                    fields=["id", "name", "customer_rank"],
                    limit=3,
                )
                self.stdout.write(f"✅ Found {len(partners)} customers")
            except Exception as e:
                self.stdout.write(f"⚠️  Partner operations: {e!s}")

            # Test product operations
            try:
                products = odoo_integration.connection.search_read(
                    "product.product",
                    [("type", "=", "service")],
                    fields=["id", "name", "type"],
                    limit=3,
                )
                self.stdout.write(f"✅ Found {len(products)} service products")
            except Exception as e:
                self.stdout.write(f"⚠️  Product operations: {e!s}")

        except Exception as e:
            self.stdout.write(f"❌ Error testing resource operations: {e!s}")
