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
    title = models.TextField()
    status = models.CharField(max_length=255)
    description = models.TextField()
    derived_from_uri = models.TextField()
    category = models.JSONField()
    code = models.JSONField()
    permitted_data_type = models.JSONField()
    body_site = models.JSONField()
    method = models.JSONField()
    permitted_unit = models.JSONField()
    component = models.JSONField()
