from django.contrib.postgres.fields import ArrayField
from django.db import models

from care.emr.models import EMRBaseModel


class ActivityDefinition(EMRBaseModel):
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
    subtitle = models.CharField(max_length=1024)
    category = models.JSONField(null=True, blank=True)
    derived_from_uri = models.TextField(null=True, blank=True)
    status = models.CharField(max_length=255)
    description = models.TextField()
    purpose = models.TextField()
    usage = models.TextField()
    kind = models.CharField(max_length=100)
    code = models.JSONField(null=True, blank=True)
    body_site = models.JSONField(null=True, blank=True)
    specimen_requirement = ArrayField(models.IntegerField(), default=list)
    observation_result_requirement = ArrayField(models.IntegerField(), default=list)
