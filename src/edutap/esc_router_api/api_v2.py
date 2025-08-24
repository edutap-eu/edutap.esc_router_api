from .models_v2 import ApiErrorMessage
from .models_v2 import CardLiteView
from .models_v2 import CardStatusView
from .models_v2 import CardUpdateView
from .models_v2 import CardView
from .models_v2 import CodeView
from .models_v2 import ContactPointView
from .models_v2 import PagedResourcesCardLiteView
from .models_v2 import PagedResourcesPersonLiteView
from .models_v2 import PageMetadata
from .models_v2 import PersonLiteView
from .models_v2 import PersonOrganisationUpdateView
from .models_v2 import PersonOrganisationView
from .models_v2 import PersonUpdateView
from .models_v2 import PersonView
from .session import session_manager
from .utils import generate_ESCN
from .utils import openapi_method
from typing import List
from typing import Literal

import json
import uuid


BASE_PATH = "/api/v2"

# --- Person -----------------------------------------------------------------


@openapi_method("GET", BASE_PATH + "/persons", "findAll")
def list_persons(
    sort: Literal["fullName", "identifier"] | None = None,
    direction: Literal["ASC", "DESC"] = "ASC",
    page: int = 0,
    size: int = 10,
    search: str | None = None,
) -> list | None:
    session = session_manager.session
    url = f"{session.base_url}{BASE_PATH}/persons"
    result: List[PersonLiteView] = []

    params = {
        "page": page,
        "size": size,
        "sort": sort,
        "direction": direction,
    }
    if search:
        params["search"] = search
    response = session.get(url=url, params=params)
    print(response)
    match response.status_code:
        case 200:
            data: PagedResourcesPersonLiteView = (
                PagedResourcesPersonLiteView.model_validate_json(response.text)
            )
            print(data.model_dump_json(indent=2))
            result = data.content
        case _:
            # 400: Bad Request --> Malformed request
            # 401: Unauthorized --> Unauthorized PIC with this Keys
            # 500: Internal Server Error --> Server Issue
            data: ApiErrorMessage = ApiErrorMessage.model_validate_json(response.text)
            print(data.model_dump_json(indent=2))
            response.raise_for_status()

    return result


@openapi_method("POST", BASE_PATH + "/persons", "create")
def add_person(
    data: PersonUpdateView | dict,
) -> PersonView | None:
    if isinstance(data, dict):
        data = PersonUpdateView.model_validate(data)

    session = session_manager.session
    url = f"{session.base_url}{BASE_PATH}/persons"
    response = session.post(url=url, data=data.model_dump_json().encode("utf-8"))

    match response.status_code:
        case 201:  # Created --> Student created
            data: PersonView = PersonView.model_validate_json(response.text)
            print(data.model_dump_json(indent=2))
            return data
        case _:
            # 400: Bad Request --> Malformed request
            # 401: Unauthorized --> Unauthorized PIC with this Keys
            # 403: Forbidden --> Unauthorized Keys
            # 409: Conflict --> European Student Identifier is already used
            # 410: Gone --> The Student with this ESI has anonymized is account
            # 500:  # Internal Server Error --> Server Issue
            data: ApiErrorMessage = ApiErrorMessage.model_validate_json(response.text)
            print(data.model_dump_json(indent=2))
            response.raise_for_status()
    return None


@openapi_method("GET", "/persons/{esi}", "findByExternalId")
def get_person(esi: uuid.UUID) -> PersonView | None:
    session = session_manager.session
    url = f"{session.base_url}{BASE_PATH}/persons/{esi}"
    response = session.get(url=url)

    match response.status_code:
        case 200:  # OK --> Entity retrieved
            data: PersonView = PersonView.model_validate_json(response.text)
            print(data.model_dump_json(indent=2))
            return data
        case _:
            # 400: Bad Request --> Malformed request
            # 401: Unauthorized --> Unauthorized PIC with this Keys
            # 403: Forbidden --> Unauthorized Keys
            # 404: Not Found --> Entity not found
            # 500: Internal Server Error --> Server Issue
            data: ApiErrorMessage = ApiErrorMessage.model_validate_json(response.text)
            print(data.model_dump_json(indent=2))
            response.raise_for_status()
    return None


@openapi_method("PUT", "/persons/{esi}")
def update_person(esi: uuid.UUID, data: dict | PersonUpdateView) -> PersonView | None:
    return None


@openapi_method("DELETE", "/persons/{esi}")
def delete_person(esi: uuid.UUID) -> bool:
    return False


def add_card(esi: uuid.UUID, data: dict | CardUpdateView) -> CardView | None:
    return None
