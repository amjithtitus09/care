def parse_fhir_property_part(part):
    code = ""
    value = None
    for subpart in part:
        if subpart["name"] == "code":
            code = subpart["valueCode"]
        elif subpart["name"] == "value":
            if "valueString" in subpart:
                value = subpart["valueString"]
            if "valueCoding" in subpart:
                value = subpart["valueCoding"]
    return {code: value}


def parse_fhir_parameter_output(parameters):
    """
    Makes a json structure from an FHIR parameter response
    """
    response = {}
    for parameter in parameters:
        value = ""
        if "valueString" in parameter:
            value = parameter["valueString"]
        if parameter["name"] == "property":
            if "property" not in response:
                response["property"] = {}
            response["property"].update(parse_fhir_property_part(parameter["part"]))
        else:
            response[parameter["name"]] = value
    return response
