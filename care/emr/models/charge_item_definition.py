from django.db import models

from care.emr.models.base import EMRBaseModel


class ChargeItemDefinition(EMRBaseModel):
    facility = models.ForeignKey(
        "facility.Facility",
        on_delete=models.PROTECT,
    )
    version = models.IntegerField(default=1)
    status = models.CharField(max_length=255)
    title = models.CharField(max_length=255)
    slug = models.CharField(max_length=255)
    derived_from_uri = models.TextField(null=True, blank=True)
    description = models.TextField(null=True, blank=True)
    purpose = models.TextField(null=True, blank=True)
    price_component = models.JSONField(default=list)
