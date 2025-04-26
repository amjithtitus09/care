from enum import Enum

from pydantic import BaseModel, model_validator

from care.emr.resources.common.coding import Coding


class MonetoryComponentType(str, Enum):
    base = "base"
    surcharge = "surcharge"
    discount = "discount"
    tax = "tax"
    informational = "informational"


class MonetoryComponent(BaseModel):
    monetory_component_type: MonetoryComponentType
    code: Coding | None = None
    factor: float | None = None
    amount: float | None = None

    @model_validator(mode="after")
    def check_amount_or_factor(self):
        if self.factor and self.amount:
            raise ValueError(
                "Only one of 'amount' or 'factor' can be present, not both."
            )
        return self
