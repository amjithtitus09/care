from datetime import datetime, timedelta

from django.db import models
from django.utils import timezone

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
    price_components = models.JSONField(default=list)
    category = models.ForeignKey(
        "emr.ChargeItemDefinitionCategory",
        on_delete=models.CASCADE,
        null=True,
        blank=True,
    )


class ChargeItemDefinitionCategory(EMRBaseModel):
    facility = models.ForeignKey(
        "facility.Facility",
        on_delete=models.PROTECT,
    )
    resource_type = models.CharField(max_length=255)
    title = models.CharField(max_length=255)
    slug = models.CharField(max_length=25)
    description = models.TextField(null=True, blank=True)
    parent = models.ForeignKey(
        "emr.ChargeItemDefinitionCategory",
        on_delete=models.CASCADE,
        null=True,
        blank=True,
    )
    cached_parent_json = models.JSONField(default=dict)

    cache_expiry_days = 15

    class Meta:
        indexes = [
            models.Index(fields=["slug", "facility"]),
        ]

    def get_parent_json(self):
        if self.parent_id:
            if self.cached_parent_json and timezone.now() < datetime.fromisoformat(
                self.cached_parent_json["cache_expiry"]
            ):
                return self.cached_parent_json
            self.parent.get_parent_json()
            self.cached_parent_json = {
                "id": str(self.parent.external_id),
                "slug": self.parent.slug,
                "name": self.parent.title,
                "description": self.parent.description,
                "parent": self.parent.cached_parent_json,
                "cache_expiry": str(
                    timezone.now() + timedelta(days=self.cache_expiry_days)
                ),
            }
            self.save(update_fields=["cached_parent_json"])
            return self.cached_parent_json
        return {}
