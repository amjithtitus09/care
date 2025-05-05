from care.emr.api.viewsets.base import EMRBaseViewSet, EMRRetrieveMixin, EMRUpdateMixin
from care.emr.models.specimen import Specimen
from care.emr.resources.specimen.spec import (
    BaseSpecimenSpec,
    SpecimenReadSpec,
    SpecimenRetrieveSpec,
    SpecimenUpdateSpec,
)


class SpecimenViewSet(EMRRetrieveMixin, EMRUpdateMixin, EMRBaseViewSet):
    database_model = Specimen
    pydantic_model = BaseSpecimenSpec
    pydantic_update_model = SpecimenUpdateSpec
    pydantic_read_model = SpecimenReadSpec
    pydantic_retrieve_model = SpecimenRetrieveSpec
    # TODO AuthZ for Retrieve and Update
