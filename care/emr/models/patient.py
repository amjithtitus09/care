from datetime import date

from dateutil.relativedelta import relativedelta
from django.contrib.postgres.fields import ArrayField
from django.core.validators import MinValueValidator
from django.db import models
from django.template.defaultfilters import pluralize
from django.utils import timezone

from care.emr.models import EMRBaseModel
from care.users.models import User
from care.utils.models.validators import mobile_or_landline_number_validator


class Patient(EMRBaseModel):
    name = models.CharField(max_length=200, default="")
    gender = models.CharField(max_length=35, default="")

    phone_number = models.CharField(
        max_length=14, validators=[mobile_or_landline_number_validator], default=""
    )

    emergency_phone_number = models.CharField(
        max_length=14, validators=[mobile_or_landline_number_validator], default=""
    )
    address = models.TextField(default="")
    permanent_address = models.TextField(default="")

    pincode = models.IntegerField(default=0, blank=True, null=True)

    date_of_birth = models.DateField(default=None, null=True)
    year_of_birth = models.IntegerField(validators=[MinValueValidator(1900)], null=True)
    deceased_datetime = models.DateTimeField(default=None, null=True, blank=True)

    marital_status = models.CharField(max_length=50, default="")

    blood_group = models.CharField(max_length=16)

    geo_organization = models.ForeignKey(
        "emr.Organization", on_delete=models.SET_NULL, null=True, blank=True
    )

    organization_cache = ArrayField(models.IntegerField(), default=list)

    users_cache = ArrayField(models.IntegerField(), default=list)

    instance_identifiers = models.JSONField(default=list, null=True, blank=True)
    facility_identifiers = models.JSONField(default=dict, null=True, blank=True)

    instance_tags = ArrayField(models.IntegerField(), default=list)
    facility_tags = models.JSONField(default=dict, null=True, blank=True)

    def get_age(self) -> str:
        start = self.date_of_birth or date(self.year_of_birth, 1, 1)
        end = (self.deceased_datetime or timezone.now()).date()

        delta = relativedelta(end, start)

        if delta.years > 0:
            year_str = f"{delta.years} year{pluralize(delta.years)}"
            return f"{year_str}"

        if delta.months > 0:
            month_str = f"{delta.months} month{pluralize(delta.months)}"
            day_str = (
                f" {delta.days} day{pluralize(delta.days)}" if delta.days > 0 else ""
            )
            return f"{month_str}{day_str}"

        if delta.days > 0:
            return f"{delta.days} day{pluralize(delta.days)}"

        return "0 days"

    def rebuild_organization_cache(self):
        organization_parents = []
        if self.geo_organization:
            organization_parents.extend(self.geo_organization.parent_cache)
            organization_parents.append(self.geo_organization.id)
        if self.id:
            for patient_organization in PatientOrganization.objects.filter(
                patient_id=self.id
            ):
                organization_parents.extend(
                    patient_organization.organization.parent_cache
                )
                organization_parents.append(patient_organization.id)

        self.organization_cache = list(set(organization_parents))

    def rebuild_users_cache(self):
        if self.id:
            users = list(
                PatientUser.objects.filter(patient=self).values_list(
                    "user_id", flat=True
                )
            )
            self.users_cache = users

    def build_instance_identifiers(self):
        self.instance_identifiers = [
            {"config": str(x.config.external_id), "value": x.value}
            for x in PatientIdentifier.objects.filter(patient=self)
        ]

    def build_facility_identifiers(self, facility_id):
        if not self.facility_identifiers:
            self.facility_identifiers = {}
        self.facility_identifiers[facility_id] = [
            {"config": str(x.config.external_id), "value": x.value}
            for x in PatientIdentifier.objects.filter(
                patient=self, config__facility_id=facility_id
            )
        ]

    def save(self, *args, **kwargs) -> None:
        if self.date_of_birth and not self.year_of_birth:
            self.year_of_birth = self.date_of_birth.year
        super().save(*args, **kwargs)
        self.rebuild_organization_cache()
        self.rebuild_users_cache()
        super().save(update_fields=["organization_cache", "users_cache"])


class PatientOrganization(EMRBaseModel):
    patient = models.ForeignKey(Patient, on_delete=models.CASCADE)
    organization = models.ForeignKey("emr.Organization", on_delete=models.CASCADE)
    # TODO : Add Role here to deny certain permissions for certain organizations

    def save(self, *args, **kwargs) -> None:
        super().save(*args, **kwargs)
        self.patient.save()


class PatientUser(EMRBaseModel):
    """
    Add a user that can access the patient
    """

    user = models.ForeignKey(User, on_delete=models.CASCADE)
    patient = models.ForeignKey(Patient, on_delete=models.CASCADE)
    role = models.ForeignKey("security.RoleModel", on_delete=models.PROTECT)

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        self.patient.save()


class PatientIdentifierConfig(EMRBaseModel):
    status = models.CharField(max_length=255)
    facility = models.ForeignKey(
        "facility.Facility", on_delete=models.CASCADE, null=True, blank=True
    )
    config = models.JSONField(default=dict, null=True, blank=True)


class PatientIdentifier(EMRBaseModel):
    facility = models.ForeignKey(
        "facility.Facility", on_delete=models.CASCADE, null=True, blank=True
    )
    patient = models.ForeignKey(Patient, on_delete=models.CASCADE)
    config = models.ForeignKey(PatientIdentifierConfig, on_delete=models.CASCADE)
    value = models.CharField(max_length=1024, db_index=True)


class PatientIdentifierConfigCache:
    """
    Configs can be cached because it changes very rarely,
    local cache makes more sense than a redis based cache interms of IO.
    Redis based alternative for this class can be implemented later if needed.
    """

    configs = {}
    instance_configs = None
    facility_configs = {}

    @classmethod
    def get_config(cls, config_id) -> PatientIdentifierConfig:
        from care.emr.resources.patient_identifier.spec import PatientIdentifierListSpec

        if config_id not in cls.configs:
            cls.configs[config_id] = PatientIdentifierListSpec.serialize(
                PatientIdentifierConfig.objects.get(external_id=config_id)
            ).to_json()
        return cls.configs[config_id]

    @classmethod
    def clear_cache(cls, config_id: int | None = None):
        if config_id is None:
            cls.configs = {}
        else:
            cls.configs.pop(config_id, None)

    @classmethod
    def get_instance_config(cls) -> list[dict]:
        from care.emr.resources.patient_identifier.spec import PatientIdentifierListSpec

        if cls.instance_configs is None:
            cls.instance_configs = [
                PatientIdentifierListSpec.serialize(x).to_json()
                for x in PatientIdentifierConfig.objects.filter(facility__isnull=True)
            ]
        return cls.instance_configs

    @classmethod
    def get_facility_config(cls, facility_id):
        from care.emr.resources.patient_identifier.spec import PatientIdentifierListSpec

        if facility_id not in cls.facility_configs:
            cls.facility_configs[facility_id] = [
                PatientIdentifierListSpec.serialize(x).to_json()
                for x in PatientIdentifierConfig.objects.filter(facility_id=facility_id)
            ]
        return cls.facility_configs[facility_id]

    @classmethod
    def clear_facility_cache(cls, facility_id):
        if cls.facility_configs:
            cls.facility_configs.pop(facility_id, None)

    @classmethod
    def clear_instance_cache(cls):
        cls.instance_configs = None
