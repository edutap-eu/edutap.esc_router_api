from typing import Literal

import uuid


class ESCN_Factory_Exception(Exception):
    pass


def generate_ESCN(pic: str, prefix: int = 1) -> uuid.UUID:
    """ """
    if len(pic) == 9 and pic.isdigit():
        node: int = int(f"{prefix:03d}{pic}", 16)
        return uuid.uuid1(node=node)
    raise ESCN_Factory_Exception("PIC is not in valid format")


def openapi_method(method: Literal["GET", "POST", "DELETE", "PUT", "PATCH"], path: str, operation_id: str | None = None):
    """ """
    BASE_PATH = "/api/v2"

    def decorator(func):
        func.__http_method__ = method.upper()
        func.__openapi_path__ = BASE_PATH + "/" + path
        func.__openapi_operation_id__ = operation_id
        return func

    return decorator
