"""
This signal is used to create a patient identifier with the same name as the patient
This allows workflows without strict Authz to function as needed
"""

from django.db.models.signals import post_save
from django.dispatch import receiver

from care.emr.models.patient import Patient, PatientIdentifier, PatientIdentifierConfig
from care.emr.resources.patient_identifier.spec import (
    IdentifierConfig,
    PatientIdentifierRetrieveConfig,
    PatientIdentifierUse,
)


class NameIdentifierConfig:
    IDENTIFIER_SYSTEM = "system.care.ohc.network/patient-name"
    CACHED_CONFIG = None

    @classmethod
    def get__or_create_system_name_identifier_config(cls):
        if cls.CACHED_CONFIG:
            return cls.CACHED_CONFIG
        identifier = PatientIdentifierConfig.objects.filter(
            config__system=cls.IDENTIFIER_SYSTEM,
            facility__isnull=True,
        ).first()
        if not identifier:
            identifier = cls.create_name_identifier()
        cls.CACHED_CONFIG = identifier
        return cls.CACHED_CONFIG

    @classmethod
    def create_name_identifier(cls):
        return PatientIdentifierConfig.objects.create(
            facility=None,
            config=IdentifierConfig(
                use=PatientIdentifierUse.secondary,
                system=cls.IDENTIFIER_SYSTEM,
                required=False,
                unique=False,
                regex="",
                display="Patient Name",
                auto_maintained=True,
                retrieve_config=PatientIdentifierRetrieveConfig(
                    retrieve_with_year_of_birth=False,
                    retrieve_with_dob=False,
                    retrieve_with_otp=False,
                    retrieve_partial_search=True,
                ),
            ).model_dump(mode="json"),
        )

    @classmethod
    def update_name_identifier(cls, patient):
        identifier = cls.get__or_create_system_name_identifier_config()
        current_identifier = PatientIdentifier.objects.filter(
            patient=patient, config=identifier
        ).first()
        if not current_identifier:
            current_identifier = PatientIdentifier.objects.create(
                patient=patient, config=identifier, value=patient.name
            )
        else:
            current_identifier.value = patient.name
            current_identifier.save()


@receiver(post_save, sender=Patient)
def update_name_identifier(sender, instance, created, **kwargs):
    NameIdentifierConfig.update_name_identifier(instance)
