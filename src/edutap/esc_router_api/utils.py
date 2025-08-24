from typing import Literal

import pycountry
import uuid


class ESCN_Factory_Exception(Exception):
    pass


class ESI_Factory_Exception(Exception):
    pass


def generate_ESCN(pic: str, prefix: int = 1) -> uuid.UUID:
    """ """
    if len(pic) == 9 and pic.isdigit() and 1 <= prefix <= 999:
        node: int = int(f"{prefix:03d}{pic}", 16)
        return uuid.uuid1(node=node)
    raise ESCN_Factory_Exception("PIC is not in valid format")


def generate_ESI(
    type: Literal["nation-wide-scope", "HEI-wide-scope"],
    student_code: str,
    cn: str | None,
    schacHomeOrganization: str | None,
) -> str:
    """ """
    esi: str
    if type == "nation-wide-scope" and cn is not None:
        if cn in [country.alpha_2 for country in pycountry.countries]:
            esi = f"urn:schac:personalUniqueCode:int:esi:{cn}:{student_code}"
        else:
            raise ESI_Factory_Exception(f"Invalid Country code: {cn}")
    elif type == "HEI-wide-scope" and schacHomeOrganization is not None:
        esi = f"urn:schac:personalUniqueCode:int:esi:{schacHomeOrganization}:{student_code}"
    else:
        raise ESI_Factory_Exception("Invalid Scope type")
    assert len(esi) <= 255, "ESI exceeds maximum length of 255 characters"
    return esi


def openapi_method(
    method: Literal["GET", "POST", "DELETE", "PUT", "PATCH"],
    path: str,
    operation_id: str | None = None,
):
    """ """

    def decorator(func):
        func.__http_method__ = method.upper()
        func.__openapi_path__ = path
        func.__openapi_operation_id__ = operation_id
        return func

    return decorator
