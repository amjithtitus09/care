from enum import Enum

from pydantic import UUID4

from care.emr.models.account import Account
from care.emr.models.charge_item import ChargeItem
from care.emr.models.invoice import Invoice
from care.emr.resources.base import EMRResource
from care.emr.resources.charge_item.spec import ChargeItemReadSpec


class InvoiceStatusOptions(str, Enum):
    draft = "draft"
    issued = "issued"
    balanced = "balanced"
    cancelled = "cancelled"
    entered_in_error = "entered_in_error"


INVOICE_CANCELLED_STATUS = [
    InvoiceStatusOptions.cancelled.value,
    InvoiceStatusOptions.entered_in_error.value,
]


class BaseInvoiceSpec(EMRResource):
    """Base model for healthcare service"""

    __model__ = Invoice
    __exclude__ = ["account", "charge_items"]

    id: UUID4 | None = None
    title: str
    status: InvoiceStatusOptions
    cancelled_reason: str | None = None
    payment_terms: str | None = None
    note: str | None = None


class InvoiceWriteSpec(BaseInvoiceSpec):
    """Invoice write specification"""

    account: UUID4
    charge_items: list[UUID4] = []

    def perform_extra_deserialization(self, is_update, obj):
        obj.account = Account.objects.get(external_id=self.account)
        obj.patient = obj.account.patient
        obj.charge_items = self.charge_items  # Rewritten in perform_create


class InvoiceReadSpec(BaseInvoiceSpec):
    """Invoice read specification"""

    @classmethod
    def perform_extra_serialization(cls, mapping, obj):
        mapping["id"] = obj.external_id


class InvoiceRetrieveSpec(InvoiceReadSpec):
    """Invoice retrieve specification"""

    charge_items: list[dict]
    total_price_component: list[dict]
    total_net: float
    total_gross: float

    @classmethod
    def perform_extra_serialization(cls, mapping, obj):
        super().perform_extra_serialization(mapping, obj)
        mapping["charge_items"] = [
            ChargeItemReadSpec.serialize(charge_item)
            for charge_item in ChargeItem.objects.filter(id__in=obj.charge_items)
        ]
