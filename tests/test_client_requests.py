"""What the client puts on the wire, and what it makes of the answer."""

import json

import pytest

from edutap.esc_router_api.models import CardUpdateView
from edutap.esc_router_api.models import PersonOrganisationUpdateView
from edutap.esc_router_api.models import PersonUpdateView


pytestmark = pytest.mark.anyio

PIC = "999978433"
ESI = "urn:schac:personalUniqueCode:int:esi:lmu.de:82683485"
ESCN = "25539be8-6423-103e-add8-988999978433"


# --- Addressing and authentication -------------------------------------------------


async def test_the_api_key_travels_as_a_bearer_token(router, client):
    router.add("GET", "/esc-rest/api/v2/persons/" + ESI, json_body={"identifier": ESI})

    await client.get_person(ESI)

    assert router.last_request.headers["Authorization"] == "Bearer test-api-key"


async def test_the_base_url_keeps_its_esc_rest_segment(router, client):
    router.add("GET", "/esc-rest/api/v2/persons/" + ESI, json_body={"identifier": ESI})

    await client.get_person(ESI)

    assert str(router.last_request.url).startswith("https://router.test/esc-rest/api/v2/")


async def test_the_public_status_endpoint_is_called_without_a_key(router, client):
    """The one operation the router serves unauthenticated.

    Sending the key anyway would work, but it would also mean a deployment with no key
    configured could not read a status -- which is the one thing it should always be
    able to do.
    """
    router.add("GET", f"/esc-rest/api/v2/cards/{ESCN}/status", json_body={"status": "ACTIVE"})

    status = await client.get_card_status(ESCN)

    assert status.status == "ACTIVE"
    assert "Authorization" not in router.last_request.headers


async def test_a_client_without_a_key_sends_no_authorization_header(router, make_client):
    router.add("GET", f"/esc-rest/api/v2/cards/{ESCN}", json_body={"cardNumber": ESCN})

    await make_client(api_key=None).get_card(ESCN)

    assert "Authorization" not in router.last_request.headers


# --- Persons -----------------------------------------------------------------------


async def test_add_person_sends_the_model_without_its_unset_fields(router, client):
    router.add("POST", "/esc-rest/api/v2/persons", status=201, json_body={"identifier": ESI})
    person = PersonUpdateView(
        identifier=ESI,
        identifierCode="ESI",
        personOrganisationUpdateViews=[
            PersonOrganisationUpdateView(organisationIdentifier=PIC, fullName="Ayten Mans")
        ],
    )

    result = await client.add_person(person)

    assert result.identifier == ESI
    sent = json.loads(router.last_request.content)
    assert sent == {
        "identifier": ESI,
        "identifierCode": "ESI",
        "personOrganisationUpdateViews": [
            {"organisationIdentifier": PIC, "fullName": "Ayten Mans"}
        ],
    }
    # `fullName` is deprecated on the person and unset here, so `exclude_none` must
    # keep it out of the body entirely rather than send an explicit null.
    assert "fullName" not in sent


async def test_add_person_accepts_a_plain_mapping(router, client):
    router.add("POST", "/esc-rest/api/v2/persons", status=201, json_body={"identifier": ESI})

    result = await client.add_person(
        {
            "identifier": ESI,
            "personOrganisationUpdateViews": [{"organisationIdentifier": PIC}],
        }
    )

    assert result.identifier == ESI


async def test_the_name_is_read_from_the_organisation_relation(router, client):
    """Where `fullName` lives after the router moved it."""
    router.add(
        "GET",
        f"/esc-rest/api/v2/persons/{ESI}",
        json_body={
            "identifier": ESI,
            "organisations": [{"fullName": "Ayten Mans", "hasPicture": True}],
        },
    )

    person = await client.get_person(ESI)

    assert person.organisations is not None
    assert person.organisations[0].fullName == "Ayten Mans"
    assert person.organisations[0].hasPicture is True


async def test_delete_person_returns_nothing_and_does_not_raise(router, client):
    router.add("DELETE", f"/esc-rest/api/v2/persons/{ESI}", status=204)

    assert await client.delete_person(ESI) is None


# --- Person pictures ---------------------------------------------------------------


async def test_get_person_image_addresses_the_organisation(router, client):
    """The organisation identifier belongs in the path.

    Earlier releases interpolated the builtin `id` here, so the request went to a path
    containing "<built-in function id>" and no picture was ever retrieved.
    """
    router.add(
        "GET",
        f"/esc-rest/api/v2/organisations/{PIC}/person/{ESI}/picture",
        content=b"\xff\xd8jpeg",
    )

    image = await client.get_person_image(PIC, ESI)

    assert image == b"\xff\xd8jpeg"
    assert (
        router.last_request.url.path == f"/esc-rest/api/v2/organisations/{PIC}/person/{ESI}/picture"
    )


async def test_add_person_image_uploads_multipart_with_the_resize_flag(router, client):
    """The router wants `multipart/form-data` with a `file` part, and answers 201.

    The previous implementation posted the raw bytes with a `Content-Type` header and
    checked for 204, so neither the request nor the success condition was right.
    """
    router.add(
        "POST",
        f"/esc-rest/api/v2/organisations/{PIC}/person/{ESI}/picture",
        status=201,
        json_body="stored",
    )

    await client.add_person_image(PIC, ESI, b"\xff\xd8jpeg", resize=True)

    request = router.last_request
    assert request.headers["content-type"].startswith("multipart/form-data")
    assert b'name="file"' in request.content
    assert b"\xff\xd8jpeg" in request.content
    assert request.url.params["resize"] == "true"


# --- Cards -------------------------------------------------------------------------


async def test_add_card_sends_the_required_fields(router, client):
    router.add("POST", "/esc-rest/api/v2/cards", status=201, json_body={"cardNumber": ESCN})
    card = CardUpdateView(
        cardStatusType="ACTIVE",
        cardType="SMART_PASSIVE",
        expiresAt="2040-12-31",
        issuedAt="2026-08-14",
        issuerIdentifier=PIC,
        personIdentifier=ESI,
    )

    result = await client.add_card(card)

    assert result.cardNumber == ESCN
    assert json.loads(router.last_request.content)["cardType"] == "SMART_PASSIVE"


async def test_generate_card_numbers_parses_the_bare_string_array(router, client):
    router.add(
        "GET",
        "/esc-rest/api/v2/cards/generate-escn",
        json_body=[ESCN, "25539be8-6423-103e-add8-988999978434"],
    )

    numbers = await client.generate_card_numbers(PIC, prefix=1, number_of_escn=2)

    assert [str(number) for number in numbers] == [
        ESCN,
        "25539be8-6423-103e-add8-988999978434",
    ]
    assert router.last_request.url.params["numberOfESCN"] == "2"


@pytest.mark.parametrize("count", [-1, 101])
async def test_generate_card_numbers_refuses_an_impossible_count(client, count):
    """Checked here rather than at the router, which answers 500 for this."""
    with pytest.raises(ValueError, match="between 0 and 100"):
        await client.generate_card_numbers(PIC, number_of_escn=count)


@pytest.mark.parametrize(
    ("accept", "expected"),
    [
        ("SVG", "image/svg+xml"),
        ("image/svg+xml", "image/svg+xml"),
        ("TEXT", "text/plain"),
        ("text/plain", "text/plain"),
    ],
)
async def test_the_qr_code_accept_header_follows_the_argument(router, client, accept, expected):
    router.add("GET", f"/esc-rest/api/v2/cards/{ESCN}/qr", content=b"<svg/>")

    await client.get_card_qr_code(ESCN, accept=accept)

    assert router.last_request.headers["Accept"] == expected


# --- Bulk card import ---------------------------------------------------------------


async def test_get_csv_config_returns_the_column_map(router, client):
    router.add(
        "GET",
        "/esc-rest/api/v2/cards/csv-config",
        json_body={"personIdentifier": 0, "cardNumber": 1},
    )

    assert await client.get_csv_config() == {"personIdentifier": 0, "cardNumber": 1}


async def test_validate_csv_uploads_the_file_and_names_the_operation(router, client):
    router.add(
        "POST",
        "/esc-rest/api/v2/cards/validate-csv",
        json_body=[{"rowNumber": 2, "fieldName": "expiresAt", "errorMessage": "in the past"}],
    )

    errors = await client.validate_csv(b"a,b\n1,2\n", operation="CREATE")

    assert errors[0].rowNumber == 2
    assert errors[0].fieldName == "expiresAt"
    assert router.last_request.url.params["operation"] == "CREATE"
    assert router.last_request.headers["content-type"].startswith("multipart/form-data")


async def test_validate_csv_returns_an_empty_list_when_the_file_is_clean(router, client):
    router.add("POST", "/esc-rest/api/v2/cards/validate-csv", json_body=[])

    assert await client.validate_csv(b"a,b\n", operation="UPDATE") == []
