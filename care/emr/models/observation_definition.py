from django.db import models

from care.emr.models import EMRBaseModel


class ObservationDefinition(EMRBaseModel):
    facility = models.ForeignKey(
        "facility.Facility",
        on_delete=models.PROTECT,
        default=None,
        null=True,
        blank=True,
    )
    version = models.IntegerField(default=1)
    slug = models.CharField(max_length=255)
    title = models.CharField(max_length=1024)
    status = models.CharField(max_length=255)
    description = models.TextField()
    derived_from_uri = models.TextField()
    category = models.JSONField()
    code = models.JSONField()
    permitted_data_type = models.CharField(max_length=100)
    body_site = models.JSONField(default=dict)
    method = models.JSONField(default=dict)
    permitted_unit = models.JSONField(default=dict)
    component = models.JSONField(default=dict)
