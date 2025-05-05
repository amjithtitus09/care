from django.conf import settings
from pydantic import UUID4, model_validator

from care.emr.models import Organization
from care.emr.resources.base import EMRResource
from care.emr.resources.common.coding import Coding
from care.emr.resources.common.monetory_component import MonetoryComponentDefinition
from care.emr.resources.organization.spec import OrganizationReadSpec
from care.emr.resources.permissions import FacilityPermissionsMixin
from care.emr.resources.user.spec import UserSpec
from care.facility.models import (
    REVERSE_FACILITY_TYPES,
    REVERSE_REVERSE_FACILITY_TYPES,
    Facility,
)


class FacilityBareMinimumSpec(EMRResource):
    __model__ = Facility
    __exclude__ = ["geo_organization"]
    id: UUID4 | None = None
    name: str


class FacilityBaseSpec(FacilityBareMinimumSpec):
    description: str
    longitude: float | None = None
    latitude: float | None = None
    pincode: int
    address: str
    phone_number: str
    middleware_address: str | None = None
    facility_type: str
    is_public: bool


DISCOUNT_CODE_COUNT_LIMIT = 100
DISCOUNT_MONETORY_COMPONENT_COUNT_LIMIT = 100


class FacilityCreateSpec(FacilityBaseSpec):
    geo_organization: UUID4
    features: list[int]
    discount_codes: list[Coding] = []
    discount_monetory_components: list[MonetoryComponentDefinition] = []

    @model_validator(mode="after")
    def validate_count(self):
        if len(self.discount_codes) >= DISCOUNT_CODE_COUNT_LIMIT:
            raise ValueError("Discount codes cannot be more than 100.")
        if (
            len(self.discount_monetory_components)
            >= DISCOUNT_MONETORY_COMPONENT_COUNT_LIMIT
        ):
            raise ValueError("Discount monetory components cannot be more than 100.")
        return self

    @model_validator(mode="after")
    def validate_codes(self):
        # Duplicate codes are not allowed
        codes = [code.code for code in self.discount_codes]
        if len(codes) != len(set(codes)):
            raise ValueError("Duplicate codes are not allowed.")
        # Redefining system codes are not allowed
        system_codes = [[code.code, code.system] for code in settings.DISCOUNT_CODES]
        for code in self.discount_codes:
            if [code.code, code.system] in system_codes:
                raise ValueError("Redefining system codes are not allowed.")
        # All monetory components code must be defined
        facility_codes = [[code.code, code.system] for code in self.discount_codes]
        all_allowed_codes = system_codes + facility_codes
        for definition in self.discount_monetory_components:
            if (
                definition.code
                and [
                    definition.code.code,
                    definition.code.system,
                ]
                not in all_allowed_codes
            ):
                raise ValueError("All monetory components code must be defined.")
        return self

    def perform_extra_deserialization(self, is_update, obj):
        obj.geo_organization = Organization.objects.filter(
            external_id=self.geo_organization, org_type="govt"
        ).first()
        obj.facility_type = REVERSE_REVERSE_FACILITY_TYPES[self.facility_type]


class FacilityReadSpec(FacilityBaseSpec):
    features: list[int]
    cover_image_url: str
    read_cover_image_url: str
    geo_organization: dict = {}

    @classmethod
    def perform_extra_serialization(cls, mapping, obj):
        mapping["id"] = obj.external_id
        mapping["read_cover_image_url"] = obj.read_cover_image_url()
        if obj.created_by:
            mapping["created_by"] = UserSpec.serialize(obj.created_by)
        mapping["facility_type"] = REVERSE_FACILITY_TYPES[obj.facility_type]
        if obj.geo_organization:
            mapping["geo_organization"] = OrganizationReadSpec.serialize(
                obj.geo_organization
            ).to_json()


class FacilityRetrieveSpec(FacilityReadSpec, FacilityPermissionsMixin):
    flags: list[str] = []
    discount_codes: list[dict] = []
    discount_monetory_components: list[dict] = []
    instance_discount_codes: list[dict] = []
    instance_discount_monetory_components: list[dict] = []
    instance_tax_codes: list[dict] = []
    instance_tax_monetory_components: list[dict] = []

    @classmethod
    def perform_extra_serialization(cls, mapping, obj):
        super().perform_extra_serialization(mapping, obj)
        mapping["flags"] = obj.get_facility_flags()
        mapping["instance_discount_codes"] = settings.DISCOUNT_CODES
        mapping["instance_discount_monetory_components"] = (
            settings.DISCOUNT_MONETORY_COMPONENT_DEFINITIONS
        )
        mapping["instance_tax_codes"] = settings.TAX_CODES
        mapping["instance_tax_monetory_components"] = (
            settings.TAX_MONETORY_COMPONENT_DEFINITIONS
        )
