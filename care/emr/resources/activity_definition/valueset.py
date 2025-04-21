from care.emr.registries.care_valueset.care_valueset import CareValueset
from care.emr.resources.common.valueset import ValueSetCompose, ValueSetInclude
from care.emr.resources.valueset.spec import ValueSetStatusOptions

ACTIVITY_DEFINITION_CATEGORY_CODE_VALUESET = CareValueset(
    "Service Request Category Code",
    "service-request-category-code",
    ValueSetStatusOptions.active.value,
)

ACTIVITY_DEFINITION_CATEGORY_CODE_VALUESET.register_valueset(
    ValueSetCompose(
        include=[
            ValueSetInclude(
                system="http://snomed.info/sct",
                concept=[
                    {"code": "108252007", "display": "Laboratory procedure"},
                    {"code": "363679005", "display": "Imaging"},
                    {"code": "409063005", "display": "Counselling"},
                    {"code": "409073007", "display": "Education"},
                    {"code": "387713003", "display": "Surgical procedure"},
                ],
            )
        ]
    )
)

ACTIVITY_DEFINITION_CATEGORY_CODE_VALUESET.register_as_system()


ACTIVITY_DEFINITION_PROCEDURE_CODE_VALUESET = CareValueset(
    "Activity Definition Procedure Code",
    "activity-definition-procedure-code",
    ValueSetStatusOptions.active.value,
)

ACTIVITY_DEFINITION_PROCEDURE_CODE_VALUESET.register_valueset(
    ValueSetCompose(
        include=[
            ValueSetInclude(
                system="http://snomed.info/sct",
                filter=[{"property": "concept", "op": "is-a", "value": "71388002"}],
            )
        ]
    )
)

ACTIVITY_DEFINITION_PROCEDURE_CODE_VALUESET.register_as_system()
