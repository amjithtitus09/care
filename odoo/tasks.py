import logging

from celery import shared_task

from odoo.integration import odoo_integration

logger = logging.getLogger(__name__)


@shared_task(bind=True, max_retries=3, default_retry_delay=60)
def sync_invoice_to_odoo_task(self, invoice_id: str):
    """
    Celery task to synchronize an invoice to Odoo.

    Args:
        invoice_id: External ID of the Django invoice

    Returns:
        Odoo invoice ID if successful, None otherwise
    """
    try:
        odoo_id = odoo_integration.sync_invoice_to_odoo(invoice_id)
        if odoo_id:
            logger.info(
                f"Task completed: Successfully synced invoice {invoice_id} to Odoo"
            )
            return odoo_id
        logger.error(f"Task failed: Failed to sync invoice {invoice_id} to Odoo")
        # Retry the task
        raise self.retry(countdown=60, max_retries=3)

    except Exception as exc:
        logger.error(f"Task error syncing invoice {invoice_id}: {exc!s}")
        # Retry the task
        raise self.retry(countdown=60, max_retries=3)


@shared_task(bind=True, max_retries=3, default_retry_delay=60)
def sync_invoice_status_task(self, invoice_id: str):
    """
    Celery task to synchronize invoice status from Odoo to Django.

    Args:
        invoice_id: External ID of the Django invoice

    Returns:
        True if successful, False otherwise
    """
    try:
        success = odoo_integration.sync_invoice_status(invoice_id)
        if success:
            logger.info(
                f"Task completed: Successfully synced status for invoice {invoice_id}"
            )
            return True
        logger.error(f"Task failed: Failed to sync status for invoice {invoice_id}")
        # Retry the task
        raise self.retry(countdown=60, max_retries=3)

    except Exception as exc:
        logger.error(f"Task error syncing status for invoice {invoice_id}: {exc!s}")
        # Retry the task
        raise self.retry(countdown=60, max_retries=3)


@shared_task(bind=True, max_retries=3, default_retry_delay=60)
def validate_odoo_invoice_task(self, invoice_id: str):
    """
    Celery task to validate (post) an invoice in Odoo.

    Args:
        invoice_id: External ID of the Django invoice

    Returns:
        True if successful, False otherwise
    """
    try:
        success = odoo_integration.validate_odoo_invoice(invoice_id)
        if success:
            logger.info(
                f"Task completed: Successfully validated invoice {invoice_id} in Odoo"
            )
            return True
        logger.error(f"Task failed: Failed to validate invoice {invoice_id} in Odoo")
        # Retry the task
        raise self.retry(countdown=60, max_retries=3)

    except Exception as exc:
        logger.error(f"Task error validating invoice {invoice_id}: {exc!s}")
        # Retry the task
        raise self.retry(countdown=60, max_retries=3)


@shared_task
def sync_all_invoices_task(limit: int = None):
    """
    Celery task to synchronize all invoices from Django to Odoo.

    Args:
        limit: Maximum number of invoices to sync

    Returns:
        Dictionary with sync results
    """
    try:
        results = odoo_integration.sync_all_invoices(limit=limit)
        logger.info(
            f"Task completed: Synced {results.get('success', 0)} invoices successfully"
        )
        return results

    except Exception as exc:
        logger.error(f"Task error syncing all invoices: {exc!s}")
        return {"success": False, "message": str(exc)}


@shared_task
def test_odoo_connection_task():
    """
    Celery task to test the Odoo connection.

    Returns:
        True if connection is successful, False otherwise
    """
    try:
        is_enabled = odoo_integration.is_enabled()
        if is_enabled:
            logger.info("Task completed: Odoo connection test successful")
        else:
            logger.warning(
                "Task completed: Odoo connection test failed - integration disabled"
            )
        return is_enabled

    except Exception as exc:
        logger.error(f"Task error testing Odoo connection: {exc!s}")
        return False
