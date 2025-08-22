from enum import Enum

from django.shortcuts import get_object_or_404
from pydantic import UUID4

from care.emr.models.patient import Patient
from care.emr.models.scheduling.token import Token, TokenCategory, TokenSubQueue
from care.emr.resources.base import EMRResource
from care.emr.resources.patient.spec import PatientListSpec
from care.emr.resources.scheduling.token_category.spec import TokenCategoryReadSpec
from care.emr.resources.scheduling.token_sub_queue.spec import TokenSubQueueReadSpec


class TokenStatusOptions(str, Enum):
    CREATED = "CREATED"
    IN_PROGRESS = "IN_PROGRESS"
    COMPLETED = "COMPLETED"
    CANCELLED = "CANCELLED"


class TokenBaseSpec(EMRResource):
    __model__ = Token
    __exclude__ = []

    id: UUID4 | None = None


class TokenGenerateSpec(TokenBaseSpec):
    patient: UUID4 | None = None
    category: UUID4
    note: str | None = None
    sub_queue: UUID4 | None = None

    def perform_extra_deserialization(self, is_update, obj):
        if self.patient:
            obj.patient = get_object_or_404(Patient, external_id=self.patient)
        obj.category = get_object_or_404(TokenCategory, external_id=self.category)
        if self.sub_queue:
            obj.sub_queue = get_object_or_404(TokenSubQueue, external_id=self.sub_queue)


class TokenUpdateSpec(TokenBaseSpec):
    status: TokenStatusOptions | None = None
    note: str | None = None
    sub_queue: UUID4 | None = None

    def perform_extra_deserialization(self, is_update, obj):
        if self.sub_queue:
            obj.sub_queue = get_object_or_404(TokenSubQueue, external_id=self.sub_queue)


class TokenReadSpec(TokenBaseSpec):
    category: dict = {}
    sub_queue: dict = {}
    note: str | None = None
    patient: dict = {}
    number: int
    status: TokenStatusOptions

    @classmethod
    def perform_extra_serialization(cls, mapping, obj):
        mapping["id"] = obj.external_id
        mapping["category"] = TokenCategoryReadSpec.serialize(obj.category).to_json()
        if obj.sub_queue:
            mapping["sub_queue"] = TokenSubQueueReadSpec.serialize(
                obj.sub_queue
            ).to_json()
        if obj.patient:
            mapping["patient"] = PatientListSpec.serialize(obj.patient).to_json()
