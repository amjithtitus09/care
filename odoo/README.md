# Odoo Integration for Django Care

This module provides a comprehensive integration between the Django Care application and Odoo ERP system, specifically focused on accounting data synchronization using Odoo's modern JSON-RPC API.

## Overview

The Odoo integration system consists of:

1. **Connection Layer**: Handles authentication and communication with Odoo using JSON-RPC
2. **Resource Layer**: Manages business logic for different Odoo models
3. **Integration Service**: Coordinates synchronization between Django and Odoo
4. **Signals**: Automatic synchronization when Django models change
5. **Management Commands**: CLI tools for testing and manual synchronization

## Features

- **Modern JSON-RPC API**: Uses Odoo's preferred JSON-RPC protocol for better performance
- **Invoice Synchronization**: Automatically sync invoices from Django to Odoo
- **Partner Management**: Create and manage customers/vendors in Odoo
- **Product Management**: Handle products and services in Odoo
- **Automatic Sync**: Real-time synchronization using Django signals
- **Async Processing**: Celery tasks for background processing
- **Error Handling**: Comprehensive error handling and retry logic
- **Caching**: Authentication and data caching for performance
- **CLI Tools**: Management commands for testing and manual operations

## Installation

1. Add the Odoo configuration to your Django settings:

```python
# settings.py

ODOO_CONFIG = {
    'base_url': 'https://your-odoo-instance.com',
    'database': 'your_database_name',
    'username': 'your_username',
    'password': 'your_password',
    'timeout': 30,
    'max_retries': 3,
    'cache_timeout': 3600,
    'enabled': True,
    'auto_sync': True,
    'async_sync': True,
}

# Add to INSTALLED_APPS
INSTALLED_APPS = [
    # ... existing apps ...
    'odoo',
]
```

2. Import the signals in your Django app configuration:

```python
# apps.py

from django.apps import AppConfig

class YourAppConfig(AppConfig):
    name = 'your_app'

    def ready(self):
        import odoo.signals
```

## Architecture

### Connection Layer

- **`OdooConnection`**: Abstract base class for Odoo connections
- **`OdooJSONRPCConnection`**: JSON-RPC implementation (modern Odoo API)

### Resource Layer

- **`OdooResource`**: Base class for Odoo model operations
- **`OdooInvoiceResource`**: Invoice-specific operations
- **`OdooPartnerResource`**: Partner/customer management
- **`OdooProductResource`**: Product and service management

### Integration Service

- **`OdooIntegrationService`**: Main service for coordinating synchronization
- Handles mapping between Django and Odoo models
- Manages partner and product creation
- Provides comprehensive error handling

## Usage

### Basic Usage

```python
from odoo.integration import odoo_integration

# Check if integration is enabled
if odoo_integration.is_enabled():
    # Sync a specific invoice
    odoo_id = odoo_integration.sync_invoice_to_odoo('invoice-external-id')

    # Sync invoice status from Odoo
    success = odoo_integration.sync_invoice_status('invoice-external-id')

    # Validate invoice in Odoo
    success = odoo_integration.validate_odoo_invoice('invoice-external-id')
```

### Using Resources Directly

```python
from odoo.connector.jsonrpc import OdooJSONRPCConnection
from odoo.resource.invoice import OdooInvoiceResource

# Create connection
connection = OdooJSONRPCConnection(
    base_url='https://your-odoo.com',
    database='your_db',
    username='your_user',
    password='your_pass'
)

# Create invoice resource
invoice_resource = OdooInvoiceResource(connection)

# Create invoice
invoice_id = invoice_resource.create_invoice(
    partner_id=1,
    invoice_date=datetime.now(),
    invoice_lines=[
        {
            'product_id': 1,
            'name': 'Consultation',
            'quantity': 1.0,
            'price_unit': 100.0,
        }
    ],
    ref='INV-001',
    narration='Medical consultation'
)
```

### Management Commands

```bash
# Test Odoo connection (basic)
python manage.py test_odoo_connection --verbose

# Test Odoo connection with operations
python manage.py test_odoo_connection --verbose --test-operations --test-resources

# Test specific Odoo operations
python manage.py test_odoo_operations

# Test operations on specific model
python manage.py test_odoo_operations --model=res.partner

# Test specific operation
python manage.py test_odoo_operations --model=res.partner --operation=search

# Test with dry run (no changes)
python manage.py test_odoo_operations --dry-run

# Sync a specific invoice from Care to Odoo
python manage.py sync_invoice invoice-external-id

# Sync with force (re-sync even if already synced)
python manage.py sync_invoice invoice-external-id --force

# Dry run to see what would be synced
python manage.py sync_invoice invoice-external-id --dry-run

# Sync and validate (post) the invoice
python manage.py sync_invoice invoice-external-id --validate

# Sync with verbose output
python manage.py sync_invoice invoice-external-id --verbose

# Sync all invoices
python manage.py sync_invoices

# Sync specific invoice (legacy command)
python manage.py sync_invoices --invoice-id=invoice-external-id

# Dry run to see what would be synced
python manage.py sync_invoices --dry-run

# Sync with limit
python manage.py sync_invoices --limit=10
```

#### Management Command Options

**test_odoo_connection:**
- `--verbose`: Show detailed connection information
- `--test-operations`: Test basic Odoo operations (search, read, etc.)
- `--test-resources`: Test resource operations (invoices, partners, products)

**test_odoo_operations:**
- `--model`: Test operations on a specific model (e.g., 'res.partner', 'account.move')
- `--operation`: Test a specific operation (search, read, create, update, delete, fields)
- `--limit`: Limit number of records to test (default: 5)
- `--dry-run`: Show what would be done without actually doing it

**sync_invoice:**
- `invoice_id`: External ID of the invoice to sync (required positional argument)
- `--force`: Force sync even if invoice already exists in Odoo
- `--dry-run`: Show what would be synced without actually syncing
- `--validate`: Validate (post) the invoice in Odoo after syncing
- `--verbose`: Show detailed information about the sync process

**sync_invoices:**
- `--invoice-id`: Sync specific invoice by external ID
- `--dry-run`: Show what would be synced without actually syncing
- `--limit`: Limit number of invoices to sync
- `--force`: Force sync even if already synced

## Automatic Synchronization

The integration automatically syncs invoices when they are created or updated in Django:

1. **Invoice Creation**: When a new invoice is created, it's automatically synced to Odoo
2. **Status Updates**: When invoice status changes, it's synced to Odoo
3. **Deletion Handling**: When an invoice is deleted, it's cancelled in Odoo

### Signal Configuration

The signals are automatically connected when the module is imported. You can control this behavior:

```python
from odoo.signals import enable_odoo_signals, disable_odoo_signals

# Enable signals (default)
enable_odoo_signals()

# Disable signals temporarily
disable_odoo_signals()
```

## Celery Tasks

For async processing, the integration provides Celery tasks:

```python
from odoo.tasks import (
    sync_invoice_to_odoo_task,
    sync_invoice_status_task,
    validate_odoo_invoice_task,
    sync_all_invoices_task,
    test_odoo_connection_task
)

# Async invoice sync
result = sync_invoice_to_odoo_task.delay('invoice-external-id')

# Async status sync
result = sync_invoice_status_task.delay('invoice-external-id')

# Test connection
result = test_odoo_connection_task.delay()
```

## JSON-RPC vs XML-RPC

This integration uses Odoo's JSON-RPC API, which offers several advantages over XML-RPC:

- **Better Performance**: JSON-RPC is generally faster than XML-RPC
- **Easier Debugging**: JSON format is more readable and easier to debug
- **Modern Protocol**: JSON-RPC is the preferred API method for Odoo
- **Better Error Handling**: More detailed error messages and better error handling
- **Session Management**: Better session handling and authentication

### API Endpoints

The JSON-RPC implementation uses these Odoo endpoints:
- `/web/session/authenticate` - Authentication
- `/web/dataset/call_kw` - Method calls
- `/web/session/destroy` - Logout

## Error Handling

The integration provides comprehensive error handling:

- **Connection Errors**: Automatic retry with exponential backoff
- **Authentication Errors**: Clear error messages and logging
- **Validation Errors**: Data validation before sending to Odoo
- **Resource Errors**: Specific error types for different operations

### Error Types

- `OdooConnectionError`: Base exception for connection issues
- `OdooAuthenticationError`: Authentication failures
- `OdooResourceError`: Resource operation failures
- `OdooResourceNotFoundError`: Resource not found
- `OdooResourceValidationError`: Data validation failures
- `OdooIntegrationError`: Integration service errors

## Configuration Options

### ODOO_CONFIG Settings

| Setting | Type | Default | Description |
|---------|------|---------|-------------|
| `base_url` | str | Required | Odoo instance URL |
| `database` | str | Required | Database name |
| `username` | str | Required | Username |
| `password` | str | Required | Password |
| `timeout` | int | 30 | Request timeout in seconds |
| `max_retries` | int | 3 | Maximum retry attempts |
| `cache_timeout` | int | 3600 | Authentication cache timeout |

### Optional Settings

| Setting | Type | Default | Description |
|---------|------|---------|-------------|
| `ODOO_ASYNC_SYNC` | bool | False | Enable async synchronization |
| `ODOO_AUTO_SYNC` | bool | True | Enable automatic synchronization |

## Data Mapping

### Invoice Mapping

| Django Field | Odoo Field | Notes |
|--------------|------------|-------|
| `external_id` | `ref` | Reference number |
| `title` | `narration` | Invoice description |
| `total_gross` | `amount_total` | Total amount |
| `total_net` | `amount_untaxed` | Net amount |
| `issue_date` | `invoice_date` | Invoice date |
| `status` | `state` | Invoice status |
| `patient` | `partner_id` | Customer/partner |
| `charge_items` | `invoice_line_ids` | Invoice lines |

### Partner Mapping

| Django Field | Odoo Field | Notes |
|--------------|------------|-------|
| `name` | `name` | Partner name |
| `phone_number` | `phone` | Phone number |
| `address` | `street` | Address |
| `facility.name` | `name` | Combined with patient name |

## Testing

### Unit Tests

```python
from django.test import TestCase
from odoo.integration import odoo_integration

class OdooIntegrationTest(TestCase):
    def test_connection(self):
        self.assertTrue(odoo_integration.is_enabled())

    def test_sync_invoice(self):
        # Create test invoice
        invoice = Invoice.objects.create(...)

        # Test sync
        odoo_id = odoo_integration.sync_invoice_to_odoo(str(invoice.external_id))
        self.assertIsNotNone(odoo_id)
```

### Integration Tests

```bash
# Test connection
python manage.py test_odoo_connection --verbose

# Test sync with dry run
python manage.py sync_invoices --dry-run --limit=5
```

## Monitoring and Logging

The integration provides comprehensive logging:

```python
import logging

# Configure logging
logging.getLogger('odoo').setLevel(logging.INFO)

# Monitor integration status
if odoo_integration.is_enabled():
    print("Odoo integration is active")
else:
    print("Odoo integration is disabled")
```

## Troubleshooting

### Common Issues

1. **Connection Failed**
   - Check Odoo URL and credentials
   - Verify network connectivity
   - Check Odoo server status

2. **Authentication Failed**
   - Verify username and password
   - Check user permissions in Odoo
   - Ensure database exists

3. **Sync Errors**
   - Check data validation
   - Verify required fields
   - Review error logs

### Debug Mode

Enable debug logging for troubleshooting:

```python
import logging
logging.getLogger('odoo').setLevel(logging.DEBUG)
```

## Security Considerations

1. **Credentials**: Store Odoo credentials securely (use environment variables)
2. **Network**: Use HTTPS for Odoo connections
3. **Permissions**: Limit Odoo user permissions to required operations
4. **Audit**: Log all integration activities for audit purposes

## Performance Optimization

1. **Caching**: Authentication tokens are cached to reduce API calls
2. **Batch Operations**: Use batch operations for multiple records
3. **Async Processing**: Use Celery tasks for background processing
4. **Connection Pooling**: Reuse connections when possible

## Contributing

When contributing to the Odoo integration:

1. Follow Django coding standards
2. Add comprehensive tests
3. Update documentation
4. Handle errors gracefully
5. Add logging for debugging

## License

This module is part of the Django Care application and follows the same license terms.
