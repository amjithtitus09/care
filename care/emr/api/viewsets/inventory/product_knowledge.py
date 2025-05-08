from django_filters import rest_framework as filters

from care.emr.api.viewsets.base import (
    EMRBaseViewSet,
    EMRCreateMixin,
    EMRListMixin,
    EMRRetrieveMixin,
    EMRUpdateMixin,
)
from care.emr.models.product_knowledge import ProductKnowledge
from care.emr.resources.product_knowledge.spec import (
    PaymentReconciliationReadSpec,
    PaymentReconciliationWriteSpec,
)


class ProductKnowledgeFilters(filters.FilterSet):
    status = filters.CharFilter(lookup_expr="iexact")
    facility = filters.UUIDFilter(field_name="facility__external_id")


class ProductKnowledgeViewSet(
    EMRCreateMixin, EMRRetrieveMixin, EMRUpdateMixin, EMRListMixin, EMRBaseViewSet
):
    database_model = ProductKnowledge
    pydantic_model = PaymentReconciliationWriteSpec
    pydantic_read_model = PaymentReconciliationReadSpec
    filterset_class = ProductKnowledgeFilters
    filter_backends = [filters.DjangoFilterBackend]
