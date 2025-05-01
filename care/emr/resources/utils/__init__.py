from pydantic import BaseModel, RootModel, model_validator

from care.emr.resources.common.coding import Coding
from care.emr.resources.common.monetory_component import MonetoryComponentDefinition


class MonetoryCodes(RootModel):
    root: list[Coding] = []

    def __iter__(self):
        return iter(self.root)

    @model_validator(mode="after")
    def check_duplicate_codes(self):
        codes = [code.code for code in self.root]
        if len(codes) != len(set(codes)):
            raise ValueError("Duplicate codes are not allowed.")
        return self


class MonetoryComponentDefinitions(RootModel):
    root: list[MonetoryComponentDefinition] = []

    @model_validator(mode="after")
    def check_duplicate_codes(self):
        codes = [definition.code.code for definition in self.root if definition.code]
        if len(codes) != len(set(codes)):
            raise ValueError("Duplicate codes are not allowed.")
        return self
