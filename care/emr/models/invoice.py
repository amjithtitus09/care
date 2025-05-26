from django.contrib.postgres.fields import ArrayField
from django.db import models

from care.emr.models import EMRBaseModel


class Invoice(EMRBaseModel):
    facility = models.ForeignKey(
        "facility.Facility",
        on_delete=models.PROTECT,
    )
    patient = models.ForeignKey(
        "emr.Patient",
        on_delete=models.PROTECT,
    )
    account = models.ForeignKey(
        "emr.Account",
        on_delete=models.PROTECT,
    )
    title = models.CharField(max_length=1024)
    status = models.CharField(max_length=100)
    cancelled_reason = models.TextField(null=True, blank=True)
    payment_terms = models.TextField(null=True, blank=True)
    note = models.TextField(null=True, blank=True)
    charge_items = ArrayField(models.IntegerField(), default=list)
    charge_items_copy = models.JSONField(default=list)
    total_price_components = models.JSONField(default=dict)
    total_net = models.FloatField(default=0)
    total_gross = models.FloatField(default=0)
    issue_date = models.DateField(null=True, blank=True, default=None)
