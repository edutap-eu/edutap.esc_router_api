from .models import ApiErrorMessage
from .models import CardLiteView
from .models import CardStatusView
from .models import CardUpdateView
from .models import CardView
from .models import PagedResourcesCardLiteView
from .models import PagedResourcesPersonLiteView
from .models import PersonLiteView
from .models import PersonUpdateView
from .models import PersonView
from .session import session_manager
from .utils import openapi_method
from annotated_types import Ge
from annotated_types import Le
from httpx import AsyncClient
from typing import Annotated
from typing import Any
from typing import Dict
from typing import List
from typing import Literal

import json
import logging
import logging.config
import uuid


LOGGING_CONFIG = {
    "version": 1,
    "handlers": {
        "default": {
            "class": "logging.StreamHandler",
            "formatter": "http",
            "stream": "ext://sys.stderr",
        }
    },
    "formatters": {
        "http": {
            "format": "%(levelname)s [%(asctime)s] %(name)s - %(message)s",
            "datefmt": "%Y-%m-%d %H:%M:%S",
        }
    },
    "loggers": {
        "httpx": {
            "handlers": ["default"],
            "level": "DEBUG",
        },
        "httpcore": {
            "handlers": ["default"],
            "level": "DEBUG",
        },
    },
}

logging.config.dictConfig(LOGGING_CONFIG)
logger = logging.getLogger("edutap.esc_router_api")
logger.setLevel(logging.DEBUG)


BASE_PATH = "/api/v2"

# --- Person -----------------------------------------------------------------


@openapi_method("GET", BASE_PATH + "/persons", "findAll")
async def list_persons(
    sort: Literal["fullName", "identifier"] | None = None,
    direction: Literal["ASC", "DESC"] = "ASC",
    page: int = 0,
    size: int = 10,
    search: str | None = None,
) -> list | None:
    """
    List all persons with pagination support.

    :param sort: Field to sort by (e.g., "fullName", "identifier").
    :param direction: Sort direction ("ASC" or "DESC").
    :param page: Page number (0-indexed).
    :param size: Number of items per page (default 10, max 100, size == 0 --> all).
    """
    result: List[PersonLiteView] = []
    client: AsyncClient = session_manager.client
    url = f"{BASE_PATH}/persons"
    is_empty: bool = False

    request_size: int = 10
    request_page: int = page
    if size == 0 or size > 10:
        request_size = 10
    else:
        request_size = size

    while request_size > 0 and not is_empty:
        params: Dict[str, Any] = {
            "page": request_page,
            "size": request_size,
            "sort": sort,
            "direction": direction,
        }
        if search:
            params["search"] = search
        response = await client.get(url=url, params=params)
        print(response)
        match response.status_code:
            case 200:
                data: PagedResourcesPersonLiteView = PagedResourcesPersonLiteView.model_validate_json(response.text)
                logger.debug(data.model_dump_json(indent=2))
                logger.info(f"Pages information: {data.page}")
                if data.content is not None:
                    result.extend(data.content)
                is_empty = data.empty is True
                if len(result) == size:
                    is_empty = True
                    request_size = 0
                elif size == 0:
                    request_page += 1
                elif len(result) < len(result) + 10 <= size:
                    request_page += 1
                elif len(result) + 10 > size:
                    request_size = size - len(result)
                    request_page += 1
            case 401:  # Unauthorized - No valid key provided
                logger.error("Unauthorized request")
                response.raise_for_status()
            case _:
                # 400: Bad Request --> Malformed request
                # 401: Unauthorized --> Unauthorized PIC with this Keys
                # 500: Internal Server Error --> Server Issue
                message: ApiErrorMessage = ApiErrorMessage.model_validate_json(response.text)
                logger.error(message.model_dump_json(indent=2))
                response.raise_for_status()
    return result


@openapi_method("POST", BASE_PATH + "/persons", "create")
async def add_person(
    data: PersonUpdateView | dict,
) -> PersonView | None:
    if isinstance(data, dict):
        input_data = PersonUpdateView.model_validate(data)
    else:
        input_data = data

    client: AsyncClient = session_manager.client
    url = f"{BASE_PATH}/persons"
    logger.debug(input_data.model_dump_json(indent=2, exclude_none=True))
    response = await client.post(
        url=url,
        json=input_data.model_dump(exclude_none=True),
    )

    match response.status_code:
        case 201:  # Created --> Student created
            result_data: PersonView = PersonView.model_validate_json(response.text)
            logger.debug(result_data.model_dump_json(indent=2))
            return result_data
        case 401:  # Unauthorized - No valid key provided
            logger.error("Unauthorized request")
            response.raise_for_status()
        case _:
            # 400: Bad Request --> Malformed request
            # 401: Unauthorized --> Unauthorized PIC with this Keys
            # 403: Forbidden --> Unauthorized Keys
            # 409: Conflict --> European Student Identifier is already used
            # 410: Gone --> The Student with this ESI has anonymized is account
            # 500:  # Internal Server Error --> Server Issue
            message: ApiErrorMessage = ApiErrorMessage.model_validate_json(response.text)
            logger.error(message.model_dump_json(indent=2))
            response.raise_for_status()
    return None


@openapi_method("GET", BASE_PATH + "/persons/{esi}", "findByExternalId")
async def get_person(esi: uuid.UUID) -> PersonView | None:
    client: AsyncClient = session_manager.client
    url = f"{BASE_PATH}/persons/{esi}"
    response = await client.get(url=url)

    match response.status_code:
        case 200:  # OK --> Entity retrieved
            data: PersonView = PersonView.model_validate_json(response.text)
            print(data.model_dump_json(indent=2))
            return data
        case 401:  # Unauthorized - No valid key provided
            logger.error("Unauthorized request")
            response.raise_for_status()
        case _:
            # 400: Bad Request --> Malformed request
            # 401: Unauthorized --> Unauthorized PIC with this Keys
            # 403: Forbidden --> Unauthorized Keys
            # 404: Not Found --> Entity not found
            # 500: Internal Server Error --> Server Issue
            message: ApiErrorMessage = ApiErrorMessage.model_validate_json(response.text)
            print(message.model_dump_json(indent=2))
            response.raise_for_status()
    return None


@openapi_method("PUT", BASE_PATH + "/persons/{esi}", "update")
async def update_person(esi: uuid.UUID, data: PersonUpdateView | dict) -> PersonView | None:
    if isinstance(data, dict):
        input_data = PersonUpdateView.model_validate(data)
    else:
        input_data = data

    client: AsyncClient = session_manager.client
    url = f"{BASE_PATH}/persons/{esi}"
    response = await client.put(
        url=url,
        json=input_data.model_dump(exclude_none=True),
    )

    match response.status_code:
        case 200:  # OK --> Entity updated
            result_data: PersonView = PersonView.model_validate_json(response.text)
            print(result_data.model_dump_json(indent=2))
            return result_data
        case 401:  # Unauthorized - No valid key provided
            logger.error("Unauthorized request")
            response.raise_for_status()
        case _:
            # 400: Bad Request --> Malformed request
            # 401: Unauthorized --> Unauthorized PIC with this Keys
            # 403: Forbidden --> Unauthorized Keys
            # 404: Not Found --> Entity not found
            # 500: Internal Server Error --> Server Issue
            message: ApiErrorMessage = ApiErrorMessage.model_validate_json(response.text)
            print(message.model_dump_json(indent=2))
            response.raise_for_status()
    return None


@openapi_method("DELETE", BASE_PATH + "/persons/{esi}", "delete")
async def delete_person(esi: uuid.UUID) -> bool:
    client: AsyncClient = session_manager.client
    url = f"{BASE_PATH}/persons/{esi}"
    response = await client.delete(url=url)

    match response.status_code:
        case 204:  # No Content --> Entity deleted
            return True
        case 401:  # Unauthorized - No valid key provided
            logger.error("Unauthorized request")
            response.raise_for_status()
        case _:
            # 400: Bad Request --> Malformed request
            # 403: Forbidden --> Unauthorized Keys
            # 404: Not Found --> Entity not found
            # 500: Internal Server Error --> Server Issue
            message: ApiErrorMessage = ApiErrorMessage.model_validate_json(response.text)
            print(message.model_dump_json(indent=2))
            response.raise_for_status()
    return False


# --- Card Management --------------------------------------------------------


@openapi_method("GET", BASE_PATH + "/cards", "findAll_1")
async def list_cards(
    sort: Literal["ESCN"] | None = None,
    direction: Literal["ASC", "DESC"] | None = None,
    page: int = 0,
    size: int = 10,
    search: str | None = None,
) -> List[CardLiteView] | None:
    result: List[CardLiteView] = []

    client: AsyncClient = session_manager.client
    url = f"{BASE_PATH}/cards"
    is_empty: bool = False

    request_size: int = 10
    request_page: int = page
    if size == 0 or size > 10:
        request_size = 10
    else:
        request_size = size

    while request_size > 0 and not is_empty:
        params: Dict[str, Any] = {
            "page": request_page,
            "size": request_size,
            "sort": sort,
            "direction": direction,
        }
        if search:
            params["search"] = search
        response = await client.get(url=url, params=params)
        print(response)
        match response.status_code:
            case 200:
                result_data: PagedResourcesCardLiteView = PagedResourcesCardLiteView.model_validate_json(response.text)
                logger.debug(result_data.model_dump_json(indent=2))
                logger.info(f"Pages information: {result_data.page}")
                if result_data.content is not None:
                    result.extend(result_data.content)
                is_empty = result_data.empty is True
                if len(result) == size:
                    is_empty = True
                    request_size = 0
                elif size == 0:
                    request_page += 1
                elif len(result) < len(result) + 10 <= size:
                    request_page += 1
                elif len(result) + 10 > size:
                    request_size = size - len(result)
                    request_page += 1
            case 401:  # Unauthorized - No valid key provided
                logger.error("Unauthorized request")
                response.raise_for_status()
            case _:
                # 400: Bad Request --> Malformed request
                # 401: Unauthorized --> Unauthorized PIC with this Keys
                # 500: Internal Server Error --> Server Issue
                message: ApiErrorMessage = ApiErrorMessage.model_validate_json(response.text)
                logger.error(message.model_dump_json(indent=2))
                response.raise_for_status()
    return result


@openapi_method("POST", BASE_PATH + "/cards", "create_1")
async def add_card(data: CardUpdateView | dict) -> CardView | None:
    input_data: CardUpdateView
    if isinstance(data, dict):
        input_data = CardUpdateView.model_validate(data)
    else:
        input_data = data

    client: AsyncClient = session_manager.client
    url = f"{BASE_PATH}/cards"
    response = await client.post(url=url, json=input_data.model_dump())

    match response.status_code:
        case 201:  # Created --> Entity created
            result_data: CardView = CardView.model_validate_json(response.text)
            print(result_data.model_dump_json(indent=2))
            return result_data
        case 401:  # Unauthorized - No valid key provided
            logger.error("Unauthorized request")
            response.raise_for_status()
        case _:
            # 400: Bad Request --> Malformed request
            # 401: Unauthorized --> Unauthorized PIC with this Keys
            # 403: Forbidden --> Unauthorized Keys
            # 404: Not Found --> Entity not found
            # 500: Internal Server Error --> Server Issue
            message: ApiErrorMessage = ApiErrorMessage.model_validate_json(response.text)
            print(message.model_dump_json(indent=2))
            response.raise_for_status()
    return None


@openapi_method("GET", BASE_PATH + "/cards/{escn}", "findByExternalId_1")
async def get_card(escn: str) -> CardView | None:
    client: AsyncClient = session_manager.client
    url = f"{BASE_PATH}/cards/{escn}"
    response = await client.get(url=url)

    match response.status_code:
        case 200:  # OK --> Entity retrieved
            data: CardView = CardView.model_validate_json(response.text)
            print(data.model_dump_json(indent=2))
            return data
        case 401:  # Unauthorized - No valid key provided
            logger.error("Unauthorized request")
            response.raise_for_status()
        case _:
            # 400: Bad Request --> Malformed request
            # 401: Unauthorized --> Unauthorized PIC with this Keys
            # 403: Forbidden --> Unauthorized Keys
            # 404: Not Found --> Entity not found
            # 500: Internal Server Error --> Server Issue
            message: ApiErrorMessage = ApiErrorMessage.model_validate_json(response.text)
            print(message.model_dump_json(indent=2))
            response.raise_for_status()
    return None


@openapi_method("DELETE", BASE_PATH + "/cards/{escn}", "delete_1")
async def delete_card(escn: str) -> bool:
    client: AsyncClient = session_manager.client
    url = f"{BASE_PATH}/cards/{escn}"
    response = await client.delete(url=url)

    match response.status_code:
        case 204:  # No Content --> Entity deleted
            print(f"Card with ID {escn} deleted successfully.")
            return True
        case 401:  # Unauthorized - No valid key provided
            logger.error("Unauthorized request")
            response.raise_for_status()
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


@openapi_method("PUT", BASE_PATH + "/cards/{escn}", "update_1")
async def update_card(escn: str, card_data: dict) -> CardView | None:
    client: AsyncClient = session_manager.client
    url = f"{BASE_PATH}/cards/{escn}"
    response = await client.put(url=url, json=card_data)

    match response.status_code:
        case 200:  # OK --> Entity updated
            data: CardView = CardView.model_validate_json(response.text)
            logger.debug(data.model_dump_json(indent=2))
            return data
        case 401:  # Unauthorized - No valid key provided
            logger.error("Unauthorized request")
            response.raise_for_status()
        case _:
            # 400: Bad Request --> Malformed request
            # 401: Unauthorized --> Unauthorized PIC with this Keys
            # 403: Forbidden --> Unauthorized Keys
            # 404: Not Found --> Entity not found
            # 500: Internal Server Error --> Server Issue
            message: ApiErrorMessage = ApiErrorMessage.model_validate_json(response.text)
            print(message.model_dump_json(indent=2))
            response.raise_for_status()
    return None


# --- Card Utilities ---------------------------------------------------------


@openapi_method("GET", BASE_PATH + "/cards/generate-escn", "getEscnList")
async def generate_card_numbers(pic: str, prefix: int = 1, numberOfESCN: Annotated[int, Ge(0), Le(100)] = 10) -> List[uuid.UUID] | None:
    """
    Generate a list of ESCN (European Student Card Numbers) based on the provided parameters.
    """
    assert 0 <= numberOfESCN <= 100, "numberOfESCN must be between 0 and 100"

    client: AsyncClient = session_manager.client
    url = f"{BASE_PATH}/cards/generate-escn"
    response = await client.get(url=url, params={"pic": pic, "prefix": prefix, "numberOfESCN": numberOfESCN})

    match response.status_code:
        case 200:  # OK --> Entity retrieved
            data: list[str] = json.loads(response.text)
            logger.debug(f"Generated ESCN: {data}")
            result = [uuid.UUID(escn) for escn in data]
            return result
        case 401:  # Unauthorized - No valid key provided
            logger.error("Unauthorized request")
            response.raise_for_status()
        case _:
            # 400: Bad Request --> Malformed request
            # 403: Forbidden --> Unauthorized Keys
            # 404: Not Found --> Entity not found
            # 500: Internal Server Error --> Server Issue
            logger.error(response)
            message: ApiErrorMessage = ApiErrorMessage.model_validate_json(response.text)
            logger.error(message.model_dump_json(indent=2))
            response.raise_for_status()
    return None


@openapi_method("GET", BASE_PATH + "/cards/{escn}/qr", "getQRCode")
async def get_card_qr_code(
    escn: uuid.UUID,
    orientation: Literal["vertical", "horizontal"] = "horizontal",
    colours: Literal["normal", "inverted"] = "normal",
    size: Literal["XS", "S", "M"] = "S",
    Accept: Literal["SVG", "TEXT", "image/svg+xml", "text/plain"] = "SVG",
) -> bytes | None:
    """
    Retrieve the QR code for a specific card in the desired format and customization options.

    :param escn: The ESCN of the card to retrieve the QR code for.
    :param orientation: Orientation of the QR code, either "vertical" or "horizontal".
    :param colours: Colour scheme of the QR code, either "normal" or "inverted".
    :param size: Size of the QR code, either "XS", "S", or "M".
    :param Accept: Desired format of the QR code, either "SVG" or "TEXT" (MIME types "image/svg+xml" or "text/plain").
    :return: QR code data in the specified format as bytes, or None if not found.

    :raises: HTTPError if the request fails due to client or server errors.
    """

    client: AsyncClient = session_manager.client
    url = f"{BASE_PATH}/cards/{escn}/qr"
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
        raise ValueError("Accept must be either 'SVG' or 'TEXT', or MIME-Types 'image/svg+xml' or 'text/plain'")
    response = await client.get(url=url, params=params, headers=headers)

    match response.status_code:
        case 200:  # OK --> Entity retrieved
            data: bytes = response.content
            return data
        case 401:  # Unauthorized - No valid key provided
            logger.error("Unauthorized request")
            response.raise_for_status()
        case _:
            # 400: Bad Request --> Malformed request
            # 401: Unauthorized --> Unauthorized PIC with this Keys
            # 403: Forbidden --> Unauthorized Keys
            # 404: Not Found --> Entity not found
            # 500: Internal Server Error --> Server Issue
            message: ApiErrorMessage = ApiErrorMessage.model_validate_json(response.text)
            print(message.model_dump_json(indent=2))
            response.raise_for_status()
    return None


@openapi_method("GET", BASE_PATH + "/cards/{escn}/status", "status")
async def get_card_status(escn: str) -> CardStatusView | None:
    """
    Retrieve the status of a specific card using its ESCN (European Student Card Number).
    :param escn: The ESCN of the card to retrieve the status for.
    :return: CardStatusView object containing the status information of the card, or None if not found.

    :raises: HTTPError if the request fails due to client or server errors.
    """

    client: AsyncClient = session_manager.client
    url = f"{BASE_PATH}/cards/{escn}/status"
    response = await client.get(url=url)
    # response = httpx.get(url=url)  # To raise HTTPError in tests

    match response.status_code:
        case 200:  # OK --> Entity retrieved
            data: CardStatusView = CardStatusView.model_validate_json(response.text)
            logger.debug(data.model_dump_json(indent=2))
            return data
        case 401:  # Unauthorized - No valid key provided
            logger.error("Unauthorized request")
            response.raise_for_status()
        case _:
            # 400: Bad Request --> Malformed request
            # 403: Forbidden --> Unauthorized Keys
            # 404: Not Found --> Entity not found
            # 500: Internal Server Error --> Server Issue
            message: ApiErrorMessage = ApiErrorMessage.model_validate_json(response.text)
            logger.error(message.model_dump_json(indent=2))
            response.raise_for_status()
    return None
