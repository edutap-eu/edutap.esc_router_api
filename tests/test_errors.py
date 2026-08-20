"""What each failure from the router turns into here."""

import httpx2
import pytest

from edutap.esc_router_api.client import ESCRouterClient
from edutap.esc_router_api.exceptions import ESCRouterAuthenticationError
from edutap.esc_router_api.exceptions import ESCRouterConflict
from edutap.esc_router_api.exceptions import ESCRouterError
from edutap.esc_router_api.exceptions import ESCRouterGone
from edutap.esc_router_api.exceptions import ESCRouterNotFound
from edutap.esc_router_api.exceptions import ESCRouterPermissionError
from edutap.esc_router_api.exceptions import ESCRouterRequestError
from edutap.esc_router_api.exceptions import ESCRouterUnavailable
from edutap.esc_router_api.exceptions import ESCRouterValidationError


pytestmark = pytest.mark.anyio

BASE_URL = "https://router.test/esc-rest"
API_KEY = "test-api-key"
ESI = "urn:schac:personalUniqueCode:int:esi:lmu.de:82683485"
PERSON_PATH = f"/esc-rest/api/v2/persons/{ESI}"


@pytest.mark.parametrize(
    ("status", "expected"),
    [
        (400, ESCRouterRequestError),
        (401, ESCRouterAuthenticationError),
        (403, ESCRouterPermissionError),
        (404, ESCRouterNotFound),
        (409, ESCRouterConflict),
        (410, ESCRouterGone),
        (422, ESCRouterValidationError),
        (429, ESCRouterValidationError),
        (500, ESCRouterUnavailable),
        (503, ESCRouterUnavailable),
    ],
)
async def test_each_status_maps_to_its_exception(router, client, status, expected):
    router.add(
        "GET",
        PERSON_PATH,
        status=status,
        json_body={"code": "E-1", "message": "no"},
    )

    with pytest.raises(expected) as raised:
        await client.get_person(ESI)

    assert raised.value.status_code == status


async def test_the_routers_error_body_is_parsed_onto_the_exception(router, client):
    router.add(
        "GET",
        PERSON_PATH,
        status=409,
        json_body={"code": "ESI_ALREADY_USED", "message": "identifier is taken"},
    )

    with pytest.raises(ESCRouterConflict) as raised:
        await client.get_person(ESI)

    assert raised.value.error is not None
    assert raised.value.error.code == "ESI_ALREADY_USED"
    assert "identifier is taken" in str(raised.value)


async def test_a_body_that_is_not_json_is_not_itself_an_error(router, client):
    """The picture endpoints answer `*/*`, and a gateway may answer HTML.

    An unparseable body must not turn a clean 404 into a parsing traceback that hides
    what the router actually said.
    """
    router.add("GET", PERSON_PATH, status=404, content=b"<html>Not Found</html>")

    with pytest.raises(ESCRouterNotFound) as raised:
        await client.get_person(ESI)

    assert raised.value.error is None
    assert raised.value.status_code == 404


async def test_gone_is_caught_as_not_found(router, client):
    """410 derives from 404 so that code written before it existed keeps working."""
    router.add("GET", PERSON_PATH, status=410, json_body={"message": "anonymised"})

    with pytest.raises(ESCRouterNotFound):
        await client.get_person(ESI)


async def test_a_redirect_is_refused_rather_than_followed(router, client):
    """Following one would hand the API key to wherever the router pointed.

    The `Authorization` header is set per request, so httpx2 has no way to know it
    should be stripped on a cross-host hop -- it only does that for headers set on the
    client itself.
    """
    router.add(
        "GET",
        PERSON_PATH,
        status=302,
        headers={"location": "https://elsewhere.test/persons"},
    )

    with pytest.raises(ESCRouterUnavailable, match="unexpected redirect"):
        await client.get_person(ESI)


async def test_a_transport_failure_becomes_unavailable():
    """A refused connection or a timeout is an outage, not a bad request."""

    def refuse(request: httpx2.Request) -> httpx2.Response:
        raise httpx2.ConnectError("connection refused", request=request)

    client = ESCRouterClient(
        base_url=BASE_URL,
        api_key=API_KEY,
        client=httpx2.AsyncClient(transport=httpx2.MockTransport(refuse)),
    )

    with pytest.raises(ESCRouterUnavailable, match="did not answer"):
        await client.get_person(ESI)


async def test_every_exception_shares_one_base(router, client):
    """One `except` clause has to be enough for a caller that only wants to log."""
    router.add("GET", PERSON_PATH, status=500, json_body={"message": "boom"})

    with pytest.raises(ESCRouterError):
        await client.get_person(ESI)
