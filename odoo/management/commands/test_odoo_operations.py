from django.core.management.base import BaseCommand, CommandError

from odoo.integration import odoo_integration


class Command(BaseCommand):
    help = "Test specific Odoo operations and resources"

    def add_arguments(self, parser):
        parser.add_argument(
            "--model",
            type=str,
            help="Test operations on a specific model (e.g., 'res.partner', 'account.move')",
        )
        parser.add_argument(
            "--operation",
            type=str,
            choices=["search", "read", "create", "update", "delete", "fields"],
            help="Test a specific operation",
        )
        parser.add_argument(
            "--limit",
            type=int,
            default=5,
            help="Limit number of records to test (default: 5)",
        )
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Show what would be done without actually doing it",
        )

    def handle(self, *args, **options):
        if not odoo_integration.is_enabled():
            raise CommandError("Odoo integration is not enabled")

        model = options["model"]
        operation = options["operation"]
        limit = options["limit"]
        dry_run = options["dry_run"]

        self.stdout.write("Testing Odoo Operations...")
        self.stdout.write("=" * 50)

        if dry_run:
            self.stdout.write("DRY RUN MODE - No changes will be made")

        try:
            if model:
                self._test_model_operations(model, operation, limit, dry_run)
            else:
                self._test_all_operations(limit, dry_run)

        except Exception as e:
            self.stdout.write(f"❌ Error during testing: {e!s}")

        self.stdout.write("=" * 50)
        self.stdout.write("Test completed.")

    def _test_model_operations(self, model, operation, limit, dry_run):
        """Test operations on a specific model."""
        self.stdout.write(f"\n🎯 Testing model: {model}")

        if operation == "fields":
            self._test_fields_operation(model)
        elif operation == "search":
            self._test_search_operation(model, limit)
        elif operation == "read":
            self._test_read_operation(model, limit)
        elif operation == "create":
            self._test_create_operation(model, dry_run)
        elif operation == "update":
            self._test_update_operation(model, limit, dry_run)
        elif operation == "delete":
            self._test_delete_operation(model, limit, dry_run)
        else:
            # Test all operations
            self._test_all_model_operations(model, limit, dry_run)

    def _test_all_operations(self, limit, dry_run):
        """Test operations on common models."""
        common_models = [
            "res.partner",
            "product.product",
            "account.move",
            "account.journal",
            "account.account",
        ]

        for model in common_models:
            try:
                self._test_all_model_operations(model, limit, dry_run)
            except Exception as e:
                self.stdout.write(f"⚠️  Error testing {model}: {e!s}")

    def _test_all_model_operations(self, model, limit, dry_run):
        """Test all operations on a model."""
        self.stdout.write(f"\n🎯 Testing model: {model}")

        # Test fields
        self._test_fields_operation(model)

        # Test search
        self._test_search_operation(model, limit)

        # Test read
        self._test_read_operation(model, limit)

        # Test create (only if not dry run)
        if not dry_run:
            self._test_create_operation(model, dry_run)

    def _test_fields_operation(self, model):
        """Test fields_get operation."""
        try:
            self.stdout.write("  📋 Testing fields operation...")
            fields = odoo_integration.connection.get_model_fields(model)
            self.stdout.write(f"    ✅ Found {len(fields)} fields")

            # Show some field names
            field_names = list(fields.keys())[:5]
            self.stdout.write(f"    📝 Sample fields: {', '.join(field_names)}")

        except Exception as e:
            self.stdout.write(f"    ❌ Fields operation failed: {e!s}")

    def _test_search_operation(self, model, limit):
        """Test search operation."""
        try:
            self.stdout.write("  🔍 Testing search operation...")
            record_ids = odoo_integration.connection.search_records(
                model, [], limit=limit
            )
            self.stdout.write(f"    ✅ Found {len(record_ids)} records")

        except Exception as e:
            self.stdout.write(f"    ❌ Search operation failed: {e!s}")

    def _test_read_operation(self, model, limit):
        """Test read operation."""
        try:
            self.stdout.write("  📖 Testing read operation...")
            records = odoo_integration.connection.search_read(model, [], limit=limit)
            self.stdout.write(f"    ✅ Read {len(records)} records")

            if records:
                # Show sample record
                sample = records[0]
                self.stdout.write(f"    📝 Sample record ID: {sample.get('id')}")

        except Exception as e:
            self.stdout.write(f"    ❌ Read operation failed: {e!s}")

    def _test_create_operation(self, model, dry_run):
        """Test create operation."""
        try:
            self.stdout.write("  ➕ Testing create operation...")

            if dry_run:
                self.stdout.write(f"    ⚠️  Would create test record in {model}")
                return

            # Create test data based on model
            test_data = self._get_test_data_for_model(model)

            if test_data:
                record_id = odoo_integration.connection.create_record(model, test_data)
                self.stdout.write(f"    ✅ Created record with ID: {record_id}")

                # Clean up - delete the test record
                odoo_integration.connection.delete_record(model, record_id)
                self.stdout.write("    🧹 Cleaned up test record")
            else:
                self.stdout.write(f"    ⚠️  No test data available for {model}")

        except Exception as e:
            self.stdout.write(f"    ❌ Create operation failed: {e!s}")

    def _test_update_operation(self, model, limit, dry_run):
        """Test update operation."""
        try:
            self.stdout.write("  ✏️  Testing update operation...")

            # Get a record to update
            records = odoo_integration.connection.search_read(model, [], limit=1)

            if not records:
                self.stdout.write("    ⚠️  No records found to update")
                return

            record_id = records[0]["id"]

            if dry_run:
                self.stdout.write(f"    ⚠️  Would update record {record_id} in {model}")
                return

            # Try to update a safe field
            update_data = {"write_date": records[0].get("write_date")}
            success = odoo_integration.connection.update_record(
                model, record_id, update_data
            )

            if success:
                self.stdout.write(f"    ✅ Updated record {record_id}")
            else:
                self.stdout.write(f"    ❌ Failed to update record {record_id}")

        except Exception as e:
            self.stdout.write(f"    ❌ Update operation failed: {e!s}")

    def _test_delete_operation(self, model, limit, dry_run):
        """Test delete operation."""
        try:
            self.stdout.write("  🗑️  Testing delete operation...")

            if dry_run:
                self.stdout.write(f"    ⚠️  Would test delete operation on {model}")
                return

            # Get a record to delete
            records = odoo_integration.connection.search_read(model, [], limit=1)

            if not records:
                self.stdout.write("    ⚠️  No records found to delete")
                return

            record_id = records[0]["id"]
            self.stdout.write(
                f"    ⚠️  Delete operation not tested for safety (record {record_id})"
            )

        except Exception as e:
            self.stdout.write(f"    ❌ Delete operation failed: {e!s}")

    def _get_test_data_for_model(self, model):
        """Get test data for creating records in different models."""
        test_data_map = {
            "res.partner": {
                "name": "Test Partner",
                "is_company": False,
            },
            "product.product": {
                "name": "Test Product",
                "type": "service",
            },
            "account.journal": {
                "name": "Test Journal",
                "code": "TEST",
                "type": "sale",
            },
        }

        return test_data_map.get(model)
