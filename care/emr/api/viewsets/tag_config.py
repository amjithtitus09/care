from care.emr.api.viewsets.base import (
    EMRBaseViewSet,
    EMRCreateMixin,
    EMRListMixin,
    EMRRetrieveMixin,
    EMRUpdateMixin,
)
from care.emr.models.tag_config import TagConfig
from care.emr.resources.tag.config_spec import (
    TagConfigReadSpec,
    TagConfigRetrieveSpec,
    TagConfigUpdateSpec,
    TagConfigWriteSpec,
)


class TagConfigViewSet(
    EMRCreateMixin, EMRRetrieveMixin, EMRUpdateMixin, EMRListMixin, EMRBaseViewSet
):
    database_model = TagConfig
    pydantic_model = TagConfigWriteSpec
    pydantic_update_model = TagConfigUpdateSpec
    pydantic_read_model = TagConfigReadSpec
    pydantic_retrieve_model = TagConfigRetrieveSpec
    # TODO AuthZ for Retrieve and Update
