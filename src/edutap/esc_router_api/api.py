from pydantic import UUID4

from .models import Student
from .models import Card
from .session import session_manager

import uuid


def generate_ESCN(prefix: int, picInstitutionCode, int) -> UUID4:
    return uuid.uuid4()


def add_student(
    data: dict | Student,
    europeanStudentIdentifier: str,
) -> dict | None:
    if isinstance(data, dict):
        data = Student.model_validate(data)

    session = session_manager.session
    url = f"{session.base_url}/students"
    response = session.post(url=url, data=data.model_dump_json().encode("utf-8"))

    if response.status_code == 500:  # Internal Server Error --> Server Issue
        raise Exception(response)
    elif response.status_code == 410:  # Gone --> The Student with this ESI has anonymized is account
        raise Exception(response)
    elif response.status_code == 403:  # Forbidden --> Unauthorized Keys
        raise Exception(response)
    elif response.status_code == 401:  # Unauthorized --> Unauthorized PIC with this Keys
        raise Exception(response)
    elif response.status_code == 409:  # Conflict --> European Student Identifier is already used
        raise Exception(response)
    elif response.status_code == 400:  # Bad Request --> Malformed request
        raise Exception(response)

    elif response.status_code == 201:  # Created --> Student created
        location = response.get("Location")
        print(location)

    return None


def list_students(offset: int = 0, limit: int = 0) -> list | None:

    session = session_manager.session
    url = f"{session.base_url}/students"
    if limit == 0:
        # read all entries
        pass
    response = session.get(url=url, params={offset:offset, limit:limit})
    if response.status_code == 500:  # Internal Server Error --> Server Issue
        raise Exception(response)
    elif response.status_code == 401:  # Unauthorized --> Unauthorized PIC with this Keys
        raise Exception(response)
    elif response.status_code == 400:  # Bad Request --> Malformed request
        raise Exception(response)

    elif response.status_code == 200:  # OK --> List of students
        location = response.headers.get("Location")
        print(location)

    return None


def get_student(europeanStudentIdentifier: UUID4) -> Student | None:
    return None


def update_student(europeanStudentIdentifier: UUID4, data: dict | Student) -> Student | None:
    return None


def delete_student(europeanStudentIdentifier: UUID4) -> bool:
    return False


def add_card(europeanStudentIdentifier: UUID4, data: dict | Card) -> Card | None:
    return None
