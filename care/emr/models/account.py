from django.db import models

from care.emr.models.base import EMRBaseModel


class Account(EMRBaseModel):
    facility = models.ForeignKey(
        "facility.Facility",
        on_delete=models.PROTECT,
    )
    status = models.CharField(max_length=255)
    billing_status = models.CharField(max_length=255)
    name = models.CharField(max_length=255)
    service_period = models.JSONField(default=dict)
    description = models.TextField(null=True, blank=True)
    patient = models.ForeignKey("emr.Patient", on_delete=models.PROTECT)
