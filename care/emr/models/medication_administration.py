from django.db import models

from care.emr.models.base import EMRBaseModel


class MedicationAdministration(EMRBaseModel):
    status = models.CharField(max_length=100)
    status_reason = models.CharField(max_length=100, null=True, blank=True)
    category = models.CharField(max_length=100, null=True, blank=True)
    medication = models.JSONField(default=dict)
    patient = models.ForeignKey(
        "facility.PatientRegistration", on_delete=models.CASCADE
    )
    encounter = models.ForeignKey(
        "facility.PatientConsultation", on_delete=models.CASCADE, null=True, blank=True
    )
    request = models.ForeignKey(
        "emr.MedicationRequest", on_delete=models.CASCADE, null=True, blank=True
    )
    authored_on = models.DateTimeField(null=True, blank=True)
    occurrence_period = models.JSONField(default=dict)
    recorded = models.DateTimeField(null=True, blank=True)
    performer = models.JSONField(default=list)
    dosage = models.JSONField(null=True, blank=True)
    note = models.TextField(null=True, blank=True)
