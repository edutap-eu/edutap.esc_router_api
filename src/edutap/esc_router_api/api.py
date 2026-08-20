"""The module-level API: one function per router operation.

Each function forwards to the process-wide client from
:func:`edutap.esc_router_api.client.get_default_client`, which builds itself from the
`ESC_*` environment on first use. That makes the short form work with no setup::

    from edutap.esc_router_api.api import get_person

    person = await get_person("urn:schac:personalUniqueCode:int:esi:DE:12345")

An application that manages its own connection pool should use
:class:`~edutap.esc_router_api.client.ESCRouterClient` directly, or install its client
once with :func:`~edutap.esc_router_api.client.set_default_client`. These functions hold
no state of their own -- there is nothing here that the class does not do.

Every function carries an :func:`~edutap.esc_router_api.utils.openapi_method`
decoration naming the operation it implements, and `tests/test_check_api_coverage.py`
checks that set against the router's OpenAPI document. An operation missing from this
module fails that test.
"""

import uuid
from collections.abc import Mapping
from typing import Any
from typing import Literal

from .client import BASE_PATH
from .client import get_default_client
from .models import CardLiteView
from .models import CardStatusView
from .models import CardUpdateView
from .models import CardView
from .models import CsvOperation
from .models import CsvValidationError
from .models import PersonLiteView
from .models import PersonUpdateView
from .models import PersonView
from .utils import openapi_method


__all__ = [
    "add_card",
    "add_person",
    "add_person_image",
    "delete_card",
    "delete_person",
    "delete_person_image",
    "generate_card_numbers",
    "get_card",
    "get_card_qr_code",
    "get_card_status",
    "get_csv_config",
    "get_person",
    "get_person_image",
    "list_cards",
    "list_persons",
    "update_card",
    "update_person",
    "validate_csv",
]


# --- Person -----------------------------------------------------------------------


@openapi_method("GET", f"{BASE_PATH}/persons", "findAll")
async def list_persons(
    sort: Literal["fullName", "identifier"] | None = None,
    direction: Literal["ASC", "DESC"] = "ASC",
    page: int = 0,
    size: int = 10,
    search: str | None = None,
) -> list[PersonLiteView]:
    """List persons. See :meth:`~edutap.esc_router_api.client.ESCRouterClient.list_persons`."""
    return await get_default_client().list_persons(
        sort=sort, direction=direction, page=page, size=size, search=search
    )


@openapi_method("POST", f"{BASE_PATH}/persons", "create")
async def add_person(data: PersonUpdateView | Mapping[str, Any]) -> PersonView:
    """Register a person with the router."""
    return await get_default_client().add_person(data)


@openapi_method("GET", f"{BASE_PATH}/persons/{{esi}}", "findByExternalId")
async def get_person(esi: str) -> PersonView:
    """Retrieve one person by European Student Identifier."""
    return await get_default_client().get_person(esi)


@openapi_method("PUT", f"{BASE_PATH}/persons/{{esi}}", "update")
async def update_person(esi: str, data: PersonUpdateView | Mapping[str, Any]) -> PersonView:
    """Replace one person's record."""
    return await get_default_client().update_person(esi, data)


@openapi_method("DELETE", f"{BASE_PATH}/persons/{{esi}}", "delete")
async def delete_person(esi: str) -> None:
    """Remove one person. Raises on failure and returns nothing on success."""
    await get_default_client().delete_person(esi)


# --- Person pictures --------------------------------------------------------------


@openapi_method(
    "GET", f"{BASE_PATH}/organisations/{{id}}/person/{{esi}}/picture", "getStudentPicture"
)
async def get_person_image(organisation_id: str, esi: str) -> bytes:
    """Download a person's picture as stored for one organisation."""
    return await get_default_client().get_person_image(organisation_id, esi)


@openapi_method(
    "POST", f"{BASE_PATH}/organisations/{{id}}/person/{{esi}}/picture", "uploadStudentPicture"
)
async def add_person_image(
    organisation_id: str,
    esi: str,
    image: bytes,
    *,
    filename: str = "picture.jpg",
    content_type: str = "image/jpeg",
    resize: bool = False,
) -> str:
    """Upload a person's picture. The router wants 200x300 pixels, or `resize=True`."""
    return await get_default_client().add_person_image(
        organisation_id,
        esi,
        image,
        filename=filename,
        content_type=content_type,
        resize=resize,
    )


@openapi_method(
    "DELETE", f"{BASE_PATH}/organisations/{{id}}/person/{{esi}}/picture", "deleteStudentPicture"
)
async def delete_person_image(organisation_id: str, esi: str) -> None:
    """Remove a person's picture for one organisation."""
    await get_default_client().delete_person_image(organisation_id, esi)


# --- Card ---------------------------------------------------------------------------


@openapi_method("GET", f"{BASE_PATH}/cards", "findAll_1")
async def list_cards(
    sort: str | None = None,
    direction: Literal["ASC", "DESC"] = "ASC",
    page: int = 0,
    size: int = 10,
    search: str | None = None,
) -> list[CardLiteView]:
    """List cards. See :meth:`~edutap.esc_router_api.client.ESCRouterClient.list_cards`."""
    return await get_default_client().list_cards(
        sort=sort, direction=direction, page=page, size=size, search=search
    )


@openapi_method("POST", f"{BASE_PATH}/cards", "create_1")
async def add_card(data: CardUpdateView | Mapping[str, Any]) -> CardView:
    """Issue a card."""
    return await get_default_client().add_card(data)


@openapi_method("GET", f"{BASE_PATH}/cards/{{escn}}", "findByExternalId_1")
async def get_card(escn: str) -> CardView:
    """Retrieve one card by its European Student Card Number."""
    return await get_default_client().get_card(escn)


@openapi_method("PUT", f"{BASE_PATH}/cards/{{escn}}", "update_1")
async def update_card(escn: str, data: CardUpdateView | Mapping[str, Any]) -> CardView:
    """Replace one card's record."""
    return await get_default_client().update_card(escn, data)


@openapi_method("DELETE", f"{BASE_PATH}/cards/{{escn}}", "delete_1")
async def delete_card(escn: str) -> None:
    """Remove one card. Raises on failure and returns nothing on success."""
    await get_default_client().delete_card(escn)


@openapi_method("GET", f"{BASE_PATH}/cards/{{escn}}/status", "status")
async def get_card_status(escn: str) -> CardStatusView:
    """Look up a card's status. The one operation that needs no API key."""
    return await get_default_client().get_card_status(escn)


@openapi_method("GET", f"{BASE_PATH}/cards/generate-escn", "getEscnList")
async def generate_card_numbers(
    pic: str, prefix: int = 1, number_of_escn: int = 10
) -> list[uuid.UUID]:
    """Ask the router to reserve card numbers, at most 100 per call."""
    return await get_default_client().generate_card_numbers(
        pic, prefix=prefix, number_of_escn=number_of_escn
    )


@openapi_method("GET", f"{BASE_PATH}/cards/{{escn}}/qr", "getQRCode")
async def get_card_qr_code(
    escn: str,
    orientation: Literal["vertical", "horizontal"] = "horizontal",
    colours: Literal["normal", "inverted"] = "normal",
    size: Literal["XS", "S", "M"] = "S",
    accept: Literal["SVG", "TEXT", "image/svg+xml", "text/plain"] = "SVG",
) -> bytes:
    """Render the QR code that points at this card's public status page."""
    return await get_default_client().get_card_qr_code(
        escn, orientation=orientation, colours=colours, size=size, accept=accept
    )


# --- Bulk card import ---------------------------------------------------------------


@openapi_method("GET", f"{BASE_PATH}/cards/csv-config", "getCsvConfig")
async def get_csv_config() -> dict[str, int]:
    """Retrieve the column layout the router expects in a card import CSV."""
    return await get_default_client().get_csv_config()


@openapi_method("POST", f"{BASE_PATH}/cards/validate-csv", "validateCsv")
async def validate_csv(
    csv_file: bytes,
    operation: CsvOperation,
    filename: str = "cards.csv",
) -> list[CsvValidationError]:
    """Check a card import file without importing it. An empty list means it passed."""
    return await get_default_client().validate_csv(csv_file, operation=operation, filename=filename)
