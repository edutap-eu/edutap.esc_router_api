from .models import Card
from .models import Student
from .session import session_manager
from .utils import generate_ESCN
from .utils import openapi_method
from typing import Literal

import uuid


# --- Person -----------------------------------------------------------------


@openapi_method("GET", "/persons")
def list_persons(offset: int = 0, limit: int = 0) -> list | None:
    session = session_manager.session
    url = f"{session.base_url}/persons"
    if limit == 0:
        # read all entries
        pass
    response = session.get(url=url, params={offset: offset, limit: limit})
    if response.status_code == 500:  # Internal Server Error --> Server Issue
        raise Exception(response)
    elif (
        response.status_code == 401
    ):  # Unauthorized --> Unauthorized PIC with this Keys
        raise Exception(response)
    elif response.status_code == 400:  # Bad Request --> Malformed request
        raise Exception(response)

    elif response.status_code == 200:  # OK --> List of students
        location = response.headers.get("Location")
        print(location)

    return None


@openapi_method("POST", "/persons")
def add_person(
    data: Person | dict,
    europeanStudentIdentifier: str,
) -> dict | None:
    if isinstance(data, dict):
        data = Student.model_validate(data)

    session = session_manager.session
    url = f"{session.base_url}/persons"
    response = session.post(url=url, data=data.model_dump_json().encode("utf-8"))

    if response.status_code == 500:  # Internal Server Error --> Server Issue
        raise Exception(response)
    elif (
        response.status_code == 410
    ):  # Gone --> The Student with this ESI has anonymized is account
        raise Exception(response)
    elif response.status_code == 403:  # Forbidden --> Unauthorized Keys
        raise Exception(response)
    elif (
        response.status_code == 401
    ):  # Unauthorized --> Unauthorized PIC with this Keys
        raise Exception(response)
    elif (
        response.status_code == 409
    ):  # Conflict --> European Student Identifier is already used
        raise Exception(response)
    elif response.status_code == 400:  # Bad Request --> Malformed request
        raise Exception(response)

    elif response.status_code == 201:  # Created --> Student created
        location = response.get("Location")
        print(location)

    return None


@openapi_method("GET", "/persons/{esi}")
def get_person(europeanStudentIdentifier: uuid.UUID) -> Student | None:
    return None


@openapi_method("PUT", "/persons/{esi}")
def update_student(
    europeanStudentIdentifier: uuid.UUID, data: dict | Student
) -> Student | None:
    return None


@openapi_method("DELETE", "/persons/{esi}")
def delete_student(europeanStudentIdentifier: uuid.UUID) -> bool:
    return False


def add_card(europeanStudentIdentifier: uuid.UUID, data: dict | Card) -> Card | None:
    return None
