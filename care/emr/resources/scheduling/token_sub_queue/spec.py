from pydantic import UUID4

from care.emr.models.scheduling.token import TokenSubQueue
from care.emr.resources.base import EMRResource
from care.emr.resources.scheduling.schedule.spec import SchedulableResourceTypeOptions


class TokenSubQueueBaseSpec(EMRResource):
    __model__ = TokenSubQueue
    __exclude__ = []

    id: UUID4 | None = None
    name: str


class TokenSubQueueCreateSpec(TokenSubQueueBaseSpec):
    resource_type: SchedulableResourceTypeOptions
    resource_id: UUID4

    def perform_extra_deserialization(self, is_update, obj):
        obj._resource_type = self.resource_type  # noqa SLF001
        obj._resource_id = self.resource_id  # noqa SLF001


class TokenSubQueueReadSpec(TokenSubQueueBaseSpec):
    @classmethod
    def perform_extra_serialization(cls, mapping, obj):
        mapping["id"] = obj.external_id
