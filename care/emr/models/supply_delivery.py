from django.db import models

from care.emr.models import EMRBaseModel


class SupplyDelivery(EMRBaseModel):
    status = models.CharField(max_length=255)
    supplied_item_quantity = models.FloatField(null=True, blank=True)
    supplied_item = models.ForeignKey("emr.Product", on_delete=models.CASCADE)
    supplied_item_condition = models.CharField(max_length=255)
    origin = models.ForeignKey(
        "emr.FacilityLocation",
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="origin_deliveries",
    )
    destination = models.ForeignKey(
        "emr.FacilityLocation",
        related_name="destination_deliveries",
        on_delete=models.CASCADE,
    )
    delivery_type = models.CharField(max_length=255)
    supply_request = models.ForeignKey(
        "emr.SupplyRequest", on_delete=models.CASCADE, null=True, blank=True
    )
