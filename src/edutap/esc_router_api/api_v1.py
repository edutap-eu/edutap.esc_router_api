from .models_v1 import Card
from .models_v1 import Student
from .session import session_manager
from .utils import generate_ESCN
from .utils import openapi_method
from pydantic import EmailStr
from pydantic import Field
from typing import List
from typing import Literal

import warnings


BASE_PATH = "/api/v1"

# --- Student Methods --------------------------------------------------------


@openapi_method("GET", "/students", "listStudents")
def list_students(offset: int = 0, limit: int = 50) -> List[Student]:
    warnings.warn(
        "list_students is deprecated and will be removed soon. Please use API v2 instead.",
        DeprecationWarning,
    )
    session = session_manager.session
    url = f"{session.base_url}{BASE_PATH}/students"
    response = session.get(url=url, params={offset: offset, limit: limit})
    if response.status_code == 500:  # Internal Server Error --> Server Issue
        raise Exception(response)
    elif response.status_code == 400:  # Bad Request --> Malformed request
        raise Exception(response)
    elif (
        response.status_code == 401
    ):  # Unauthorized --> Unauthorized PIC with this Keys
        raise Exception(response)
    elif response.status_code == 403:  # Forbidden --> Access denied
        raise Exception(response)
    elif response.status_code == 200:  # OK --> List of students
        print(response)

    return None


def add_student(
    emailAddress: EmailStr,
    europeanStudentIdentifier: str = Field(
        pattern=r"^\d{1,10}$", description="European Student Identifier"
    ),
    name: str | None = None,
):
    warnings.warn(
        "add_student is deprecated and will be removed soon. Please use API v2 instead.",
        DeprecationWarning,
    )
    pass


def get_student():
    warnings.warn(
        "get_student is deprecated and will be removed soon. Please use API v2 instead.",
        DeprecationWarning,
    )
    pass


def update_student():
    warnings.warn(
        "update_student is deprecated and will be removed soon. Please use API v2 instead.",
        DeprecationWarning,
    )
    pass


def delete_student():
    warnings.warn(
        "delete_student is deprecated and will be removed soon. Please use API v2 instead.",
        DeprecationWarning,
    )
    pass


# --- Card Methods -----------------------------------------------------------


def list_cards():
    warnings.warn(
        "list_cards is deprecated and will be removed soon. Please use API v2 instead.",
        DeprecationWarning,
    )
    pass


def add_card():
    warnings.warn(
        "add_card is deprecated and will be removed soon. Please use API v2 instead.",
        DeprecationWarning,
    )
    pass


def get_card():
    warnings.warn(
        "get_card is deprecated and will be removed soon. Please use API v2 instead.",
        DeprecationWarning,
    )
    pass


def delete_card():
    warnings.warn(
        "delete_card is deprecated and will be removed soon. Please use API v2 instead.",
        DeprecationWarning,
    )
    pass
