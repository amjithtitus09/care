import json

from care.emr.fhir.resources.base import ResourceManger
from care.emr.fhir.resources.code_concept import MinimalCodeConcept
from care.emr.fhir.resources.code_system import CodeSystem


class ValueSetResource(ResourceManger):
    allowed_properties = ["include", "exclude", "search", "count"]

    def serialize(self, result):
        return MinimalCodeConcept(system=result["system"], code=result["code"], display=result["display"])

    def search(self):
        parameters = []
        for key in self._filters:
            if key == "search":
                parameters.append({"name": "filter", "valueString": self._filters[key]})
            if key == "count":
                parameters.append({"name": "count", "valueInteger": self._filters[key]})
        parameters.append(
            {
                "name": "valueSet",
                "resource": {
                    "resourceType": "ValueSet",
                    "compose": {
                        "include": self._filters.get("include", []),
                        "exclude": self._filters.get("exclude", []),
                    },
                },
            }
        )
        request_json = {"resourceType": "Parameters", "parameter": parameters}
        full_result = self.query("POST", "ValueSet/$expand", request_json)
        results = full_result["expansion"]
        if "contains" not in results:
            return []
        return self.handle_list(results["contains"])
