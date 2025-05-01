import environ

from care.emr.resources.utils import MonetoryCodes, MonetoryComponentDefinitions

env = environ.Env()

MAX_APPOINTMENTS_PER_PATIENT = env.int("MAX_APPOINTMENTS_PER_PATIENT", default=10)

MAX_ACTIVE_ENCOUNTERS_PER_PATIENT = env.int(
    "MAX_ACTIVE_ENCOUNTERS_PER_PATIENT", default=5
)

# Maximum file upload size in MB
MAX_FILE_UPLOAD_SIZE = env.int("MAX_FILE_UPLOAD_SIZE", default=5)

LOCATION_MAX_DEPTH = env.int("LOCATION_MAX_DEPTH", default=10)

ORGANIZATION_MAX_DEPTH = env.int("ORGANIZATION_MAX_DEPTH", default=10)

FACILITY_ORGANIZATION_MAX_DEPTH = env.int("FACILITY_ORGANIZATION_MAX_DEPTH", default=10)

MAX_LOCATION_IN_FACILITY = env.int("MAX_LOCATION_IN_FACILITY", default=1000)

MAX_ORGANIZATION_IN_FACILITY = env.int("MAX_ORGANIZATION_IN_FACILITY", default=1000)

MAX_QUESTIONNAIRE_TEXT_RESPONSE_SIZE = env.int(
    "MAX_QUESTIONNAIRE_TEXT_RESPONSE_SIZE", default=2500
)

TAX_CODES = MonetoryCodes(
    env.json(
        "TAX_CODES",
        default=[
            {
                "code": "igst",
                "display": "IGST",
                "system": "http://ohc.network/codes/monetory/tax",
            },
            {
                "code": "gst",
                "display": "GST",
                "system": "http://ohc.network/codes/monetory/tax",
            },
            {
                "code": "sgst",
                "display": "SGST",
                "system": "http://ohc.network/codes/monetory/tax",
            },
        ],
    )
)

TAX_MONETORY_COMPONENT_DEFINITIONS = MonetoryComponentDefinitions(
    env.json(
        "TAX_MONETORY_COMPONENT_DEFINITIONS",
        default=[
            {
                "title": "IGST",
                "code": {
                    "code": "igst",
                    "display": "IGST",
                    "system": "http://ohc.network/codes/monetory/tax",
                },
                "monetory_component_type": "tax",
                "factor": 10,
            },
            {
                "title": "GST",
                "code": {
                    "code": "gst",
                    "display": "GST",
                    "system": "http://ohc.network/codes/monetory/tax",
                },
                "monetory_component_type": "tax",
                "factor": 10,
            },
        ],
    )
)

DISCOUNT_CODES = MonetoryCodes(
    env.json(
        "DISCOUNT_CODES",
        default=[
            {
                "code": "oldage",
                "display": "Old Age Discount",
                "system": "http://ohc.network/codes/monetory/discount",
            },
            {
                "code": "child",
                "display": "Child Discount",
                "system": "http://ohc.network/codes/monetory/discount",
            },
            {
                "code": "student",
                "display": "Student Discount",
                "system": "http://ohc.network/codes/monetory/discount",
            },
        ],
    )
)

DISCOUNT_MONETORY_COMPONENT_DEFINITIONS = MonetoryComponentDefinitions(
    env.json(
        "DISCOUNT_MONETORY_COMPONENT_DEFINITIONS",
        default=[
            {
                "title": "Old Age Discount ?",
                "code": {
                    "code": "oldage",
                    "display": "Old Age Discount",
                    "system": "http://ohc.network/codes/monetory/discount",
                },
                "monetory_component_type": "discount",
                "factor": 10,
            },
            {
                "title": "Child Discount ?",
                "code": {
                    "code": "child",
                    "display": "Child Discount",
                    "system": "http://ohc.network/codes/monetory/discount",
                },
                "monetory_component_type": "discount",
                "factor": 10,
            },
        ],
    )
)
