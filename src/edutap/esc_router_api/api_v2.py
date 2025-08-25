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

import httpx
import json
import logging
import uuid


logger = logging.getLogger("edutap.esc_router_api")
logger.setLevel(logging.DEBUG)

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
    logger.debug(data.model_dump_json(indent=2, exclude_none=True))
    response = session.post(
        url=url,
        json=data.model_dump_json(exclude_none=True),
    )

    match response.status_code:
        case 201:  # Created --> Student created
            data: PersonView = PersonView.model_validate_json(response.text)
            logger.debug(data.model_dump_json(indent=2))
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
            logger.error(data.model_dump_json(indent=2))
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
def update_person(esi: uuid.UUID, data: PersonUpdateView | dict) -> PersonView | None:
    if isinstance(data, dict):
        data = PersonUpdateView.model_validate(data)

    session = session_manager.session
    url = f"{session.base_url}{BASE_PATH}/persons/{esi}"
    response = session.put(url=url, data=data.model_dump_json().encode("utf-8"))

    match response.status_code:
        case 200:  # OK --> Entity updated
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


@openapi_method("DELETE", "/persons/{esi}")
def delete_person(esi: uuid.UUID) -> bool:
    session = session_manager.session
    url = f"{session.base_url}{BASE_PATH}/persons/{esi}"
    response = session.delete(url=url)

    match response.status_code:
        case 204:  # No Content --> Entity deleted
            return True
        case _:
            # 400: Bad Request --> Malformed request
            # 401: Unauthorized --> Unauthorized PIC with this Keys
            # 403: Forbidden --> Unauthorized Keys
            # 404: Not Found --> Entity not found
            # 500: Internal Server Error --> Server Issue
            data: ApiErrorMessage = ApiErrorMessage.model_validate_json(response.text)
            print(data.model_dump_json(indent=2))
            response.raise_for_status()
    return False


# --- Card Management --------------------------------------------------------


@openapi_method("GET", "/cards", "findAll_1'")
def list_cards(
    sort: Literal["ESCN"] | None = None,
    direction: Literal["ASC", "DESC"] | None = None,
    page: int = 0,
    size: int = 10,
    search: str | None = None,
) -> List[CardLiteView] | None:
    session = session_manager.session
    url = f"{session.base_url}{BASE_PATH}/cards"
    params = {"sort": sort, "direction": direction, "page": page, "size": size}
    response = session.get(url=url, params=params)
    result: List[CardLiteView] = []
    logger.debug(f"Request URL: {url}")
    logger.debug(f"Request Params: {params}")

    match response.status_code:
        case 200:  # OK --> Entity retrieved
            data: PagedResourcesCardLiteView = (
                PagedResourcesCardLiteView.model_validate_json(response.text)
            )
            logger.debug(data.model_dump_json(indent=2))
            if data.empty is False:
                print("Retrieved cards:")
                cards = [card for card in data.content]
                for card in cards:
                    print(card.model_dump_json(indent=2))
                    result.append(card)
        case _:
            # 400: Bad Request --> Malformed request
            # 401: Unauthorized --> Unauthorized PIC with this Keys
            # 403: Forbidden --> Unauthorized Keys
            # 404: Not Found --> Entity not found
            # 500: Internal Server Error --> Server Issue
            data: ApiErrorMessage = ApiErrorMessage.model_validate_json(response.text)
            logger.error(data.model_dump_json(indent=2))
            response.raise_for_status()
    return result


@openapi_method("POST", "/persons/{esi}/cards", "createCard")
def add_card(esi: uuid.UUID, data: dict | CardUpdateView) -> CardView | None:
    if isinstance(data, dict):
        data = CardUpdateView.model_validate(data)

    session = session_manager.session
    url = f"{session.base_url}{BASE_PATH}/persons/{esi}/cards"
    response = session.post(url=url, data=data.model_dump_json().encode("utf-8"))

    match response.status_code:
        case 201:  # Created --> Entity created
            data: CardView = CardView.model_validate_json(response.text)
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


@openapi_method("GET", "/cards/generate-escn", "getEscnList")
def generate_card_numbers(
    pic: str, prefix: int = 1, numberOfESCN: int = 1
) -> List[uuid.UUID] | None:
    """
    Generate a list of ESCN (European Student Card Numbers) based on the provided parameters.
    """
    session = session_manager.session
    url = f"{session.base_url}{BASE_PATH}/cards/generate-escn"
    response = session.get(
        url=url, params={"pic": pic, "prefix": prefix, "numberOfESCN": numberOfESCN}
    )

    match response.status_code:
        case 200:  # OK --> Entity retrieved
            data: list[uuid.UUID] = json.loads(response.text)
            print(f"Generated ESCN: {data}")
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


@openapi_method("GET", "/cards/{cardId}", "findById")
def get_card(card_id: str) -> CardView | None:
    session = session_manager.session
    url = f"{session.base_url}{BASE_PATH}/cards/{card_id}"
    response = session.get(url=url)

    match response.status_code:
        case 200:  # OK --> Entity retrieved
            data: CardView = CardView.model_validate_json(response.text)
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


@openapi_method("DELETE", "/cards/{cardId}", "deleteById")
def delete_card(card_id: str) -> bool:
    session = session_manager.session
    url = f"{session.base_url}{BASE_PATH}/cards/{card_id}"
    response = session.delete(url=url)

    match response.status_code:
        case 204:  # No Content --> Entity deleted
            print(f"Card with ID {card_id} deleted successfully.")
            return True
        case _:
            # 400: Bad Request --> Malformed request
            # 401: Unauthorized --> Unauthorized PIC with this Keys
            # 403: Forbidden --> Unauthorized Keys
            # 404: Not Found --> Entity not found
            # 500: Internal Server Error --> Server Issue
            data: ApiErrorMessage = ApiErrorMessage.model_validate_json(response.text)
            print(data.model_dump_json(indent=2))
            response.raise_for_status()
    return False


@openapi_method("PUT", "/cards/{cardId}", "updateById")
def update_card(card_id: str, card_data: dict) -> CardView | None:
    session = session_manager.session
    url = f"{session.base_url}{BASE_PATH}/cards/{card_id}"
    response = session.put(url=url, json=card_data)

    match response.status_code:
        case 200:  # OK --> Entity updated
            data: CardView = CardView.model_validate_json(response.text)
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


@openapi_method("GET", "/cards/{cardId}/qr", "getCardQrCode")
def get_card_qr_code(
    escn: uuid.UUID,
    orientation: Literal["vertical", "horizontal"] = "horizontal",
    colours: Literal["normal", "inverted"] = "normal",
    size: Literal["XS", "S", "M"] = "S",
    Accept: Literal["SVG", "TEXT", "image/svg+xml", "text/plain"] = "SVG",
) -> bytes | None:
    session = session_manager.session
    url = f"{session.base_url}{BASE_PATH}/cards/{escn}/qr"
    params = {
        "orientation": orientation,
        "colours": colours,
        "size": size,
    }
    if Accept == "SVG" or Accept == "image/svg+xml":
        headers = {"Accept": "image/svg+xml"}
    elif Accept == "TEXT" or Accept == "text/plain":
        headers = {"Accept": "text/plain"}
    else:
        raise ValueError(
            "Accept must be either 'SVG' or 'TEXT', or MIME-Types 'image/svg+xml' or 'text/plain'"
        )
    response = session.get(url=url, params=params, headers=headers)

    match response.status_code:
        case 200:  # OK --> Entity retrieved
            data: bytes = response.content
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


@openapi_method("GET", "/cards/{escn}/status", "getCardStatus")
def get_card_status(escn: str) -> CardStatusView | None:
    session = session_manager.session
    url = f"{session.base_url}{BASE_PATH}/cards/{escn}/status"
    response = session.get(url=url)
    response = httpx.get(url=url)  # To raise HTTPError in tests

    match response.status_code:
        case 200:  # OK --> Entity retrieved
            data: CardStatusView = CardStatusView.model_validate_json(response.text)
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
