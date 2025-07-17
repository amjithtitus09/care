import logging

from django.conf import settings
from django.db.models.signals import post_delete, post_save
from django.dispatch import receiver

from odoo.integration import odoo_integration

logger = logging.getLogger(__name__)


@receiver(post_save, sender=None)
def sync_invoice_to_odoo(sender, instance, created, **kwargs):
    """
    Signal handler to automatically sync invoices to Odoo when they are created or updated.

    Args:
        sender: The model class (Invoice)
        instance: The actual instance being saved
        created: Boolean indicating if this is a new instance
        **kwargs: Additional keyword arguments
    """
    # Import here to avoid circular imports
    from care.emr.models.invoice import Invoice

    # Check if this is an Invoice instance
    if not isinstance(instance, Invoice):
        return

    # Check if Odoo integration is enabled
    if not odoo_integration.is_enabled():
        return

    # Only sync if this is a new invoice or if the status has changed
    if created or instance.tracker.has_changed("status"):
        try:
            # Use Celery task for async processing if available
            if hasattr(settings, "ODOO_ASYNC_SYNC") and settings.ODOO_ASYNC_SYNC:
                from odoo.tasks import sync_invoice_to_odoo_task

                sync_invoice_to_odoo_task.delay(str(instance.external_id))
            else:
                # Sync synchronously
                odoo_id = odoo_integration.sync_invoice_to_odoo(
                    str(instance.external_id)
                )
                if odoo_id:
                    logger.info(
                        f"Successfully synced invoice {instance.external_id} to Odoo"
                    )
                else:
                    logger.warning(
                        f"Failed to sync invoice {instance.external_id} to Odoo"
                    )

        except Exception as e:
            logger.error(f"Error syncing invoice {instance.external_id} to Odoo: {e!s}")


@receiver(post_delete, sender=None)
def handle_invoice_deletion(sender, instance, **kwargs):
    """
    Signal handler to handle invoice deletion in Odoo.

    Args:
        sender: The model class (Invoice)
        instance: The actual instance being deleted
        **kwargs: Additional keyword arguments
    """
    # Import here to avoid circular imports
    from care.emr.models.invoice import Invoice

    # Check if this is an Invoice instance
    if not isinstance(instance, Invoice):
        return

    # Check if Odoo integration is enabled
    if not odoo_integration.is_enabled():
        return

    # Check if we have an Odoo invoice ID
    odoo_invoice_id = instance.meta.get("odoo_invoice_id") if instance.meta else None

    if odoo_invoice_id:
        try:
            # Cancel the invoice in Odoo instead of deleting it
            # This preserves the audit trail
            success = odoo_integration.invoice_resource.cancel_invoice(odoo_invoice_id)
            if success:
                logger.info(
                    f"Cancelled Odoo invoice {odoo_invoice_id} for deleted Django invoice {instance.external_id}"
                )
            else:
                logger.warning(f"Failed to cancel Odoo invoice {odoo_invoice_id}")

        except Exception as e:
            logger.error(f"Error cancelling Odoo invoice {odoo_invoice_id}: {e!s}")


def enable_odoo_signals():
    """
    Enable Odoo integration signals.
    This function should be called during Django startup.
    """
    # Import here to avoid circular imports
    from care.emr.models.invoice import Invoice

    # Connect the signals
    post_save.connect(sync_invoice_to_odoo, sender=Invoice)
    post_delete.connect(handle_invoice_deletion, sender=Invoice)
    logger.info("Odoo integration signals enabled")


def disable_odoo_signals():
    """
    Disable Odoo integration signals.
    This function can be used to temporarily disable signals.
    """
    # Import here to avoid circular imports
    from care.emr.models.invoice import Invoice

    # Disconnect the signals
    post_save.disconnect(sync_invoice_to_odoo, sender=Invoice)
    post_delete.disconnect(handle_invoice_deletion, sender=Invoice)
    logger.info("Odoo integration signals disabled")
