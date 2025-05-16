from django.db import models

from care.emr.models.base import EMRBaseModel
from care.emr.models.medication_request import MedicationRequest


class MedicationDispense(EMRBaseModel):
    status = models.CharField(max_length=100)
    not_performed_reason = models.CharField(max_length=100, null=True, blank=True)
    category = models.CharField(max_length=100, null=True, blank=True)
    when_prepared = models.DateTimeField(null=True, blank=True)
    when_handed_over = models.DateTimeField(null=True, blank=True)
    note = models.TextField(null=True, blank=True)
    dosage_instruction = models.JSONField(default=dict, null=True, blank=True)
    substitution = models.JSONField(default=dict, null=True, blank=True)
    encounter = models.ForeignKey("emr.Encounter", on_delete=models.CASCADE)
    patient = models.ForeignKey("emr.Patient", on_delete=models.CASCADE)
    location = models.ForeignKey("emr.FacilityLocation", on_delete=models.CASCADE)
    authorizing_prescription = models.ForeignKey(
        MedicationRequest, on_delete=models.SET_NULL, null=True, blank=True
    )
    item = models.ForeignKey("emr.InventoryItem", on_delete=models.CASCADE)
    charge_item = models.ForeignKey(
        "emr.ChargeItem", on_delete=models.CASCADE, null=True, blank=True
    )
    quantity = models.FloatField()
    days_supply = models.FloatField()
