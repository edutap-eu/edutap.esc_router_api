from .session import session_manager
from .models_v2 import PagedResourcesPersonLiteView
from .utils import generate_ESCN
from .utils import openapi_method
from typing import Literal
from httpx import HTTPError

import uuid


BASE_PATH = "/api/v2"

# --- Person -----------------------------------------------------------------


@openapi_method("GET", BASE_PATH + "/persons", "findAll")
def list_persons(sort: bool = False, direction: Literal["ASC", "DESC"] = "ASC", page: int = 0, size: int = 10, search: str | None = None) -> list | None:
    session = session_manager.session
    url = f"{session.base_url}{BASE_PATH}/persons"
    if size == 0:
        # read all entries
        pass
    params = {
        "page": page,
        "size": size,
        "sort": sort,
        "direction": direction,
    }
    if search:
        params["search"] = search
    response = session.get(url=url, params=params)
    if response.status_code == 500:  # Internal Server Error --> Server Issue
        response.raise_for_status()
    elif (
        response.status_code == 401
    ):  # Unauthorized --> Unauthorized PIC with this Keys
        response.raise_for_status()
    elif response.status_code == 400:  # Bad Request --> Malformed request
        response.raise_for_status()

    elif response.status_code == 200:  # OK --> List of students
        data: PagedResourcesPersonLiteView = PagedResourcesPersonLiteView.model_validate_json(response.text())
        print(data)


    return None


@openapi_method("POST", "/persons")
def add_person(
    data: Person | dict,
    europeanStudentIdentifier: str,
) -> dict | None:
    if isinstance(data, dict):
        data = Student.model_validate(data)

    session = session_manager.session
    url = f"{session.base_url}{BASE_PATH}/persons"
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
