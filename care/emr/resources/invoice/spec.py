from enum import Enum

from pydantic import UUID4

from care.emr.models.account import Account
from care.emr.models.invoice import Invoice
from care.emr.resources.base import EMRResource


class InvoiceStatusOptions(str, Enum):
    draft = "draft"
    issued = "issued"
    balanced = "balanced"
    cancelled = "cancelled"
    entered_in_error = "entered_in_error"


class BaseInvoiceSpec(EMRResource):
    """Base model for healthcare service"""

    __model__ = Invoice
    __exclude__ = ["account"]

    id: UUID4 | None = None
    title: str
    status: InvoiceStatusOptions
    cancelled_reason: str | None = None
    payment_terms: str | None = None
    note: str | None = None


class InvoiceWriteSpec(BaseInvoiceSpec):
    """Invoice write specification"""

    account: UUID4

    def perform_extra_deserialization(self, is_update, obj):
        obj.account = Account.objects.get(external_id=self.account)
        obj.patient = obj.account.patient


class InvoiceReadSpec(BaseInvoiceSpec):
    """Invoice read specification"""

    @classmethod
    def perform_extra_serialization(cls, mapping, obj):
        mapping["id"] = obj.external_id
