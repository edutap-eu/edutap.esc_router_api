"""The process-wide client behind the module-level API."""

import httpx2
import pytest

from edutap.esc_router_api import api
from edutap.esc_router_api.client import ESCRouterClient
from edutap.esc_router_api.client import close_default_client
from edutap.esc_router_api.client import get_default_client
from edutap.esc_router_api.client import set_default_client


pytestmark = pytest.mark.anyio

ESI = "urn:schac:personalUniqueCode:int:esi:lmu.de:82683485"


@pytest.fixture(autouse=True)
def _no_leaked_default_client():
    """Leave the process-wide slot as it was found.

    Without this, a test that installs a client would decide what every later test in
    the session talks to.
    """
    set_default_client(None)
    yield
    set_default_client(None)


def test_the_default_client_is_built_once(monkeypatch):
    monkeypatch.setenv("ESC_API_KEY", "from-the-environment")

    assert get_default_client() is get_default_client()


def test_an_installed_client_is_used_as_is(client):
    set_default_client(client)

    assert get_default_client() is client


async def test_the_module_level_api_goes_through_the_installed_client(router, client):
    """This is the whole contract of `api`: no state of its own, just the client."""
    set_default_client(client)
    router.add("GET", f"/esc-rest/api/v2/persons/{ESI}", json_body={"identifier": ESI})

    person = await api.get_person(ESI)

    assert person.identifier == ESI
    assert router.last_request.headers["Authorization"] == "Bearer test-api-key"


async def test_closing_the_default_client_clears_the_slot(monkeypatch):
    monkeypatch.setenv("ESC_API_KEY", "from-the-environment")
    first = get_default_client()

    await close_default_client()

    assert get_default_client() is not first


async def test_closing_when_none_was_built_is_harmless():
    await close_default_client()


async def test_a_borrowed_http_client_survives_aclose():
    """Closing a client that was handed in would take down the caller's pool.

    A FastAPI application shares one `httpx2.AsyncClient` across everything it talks
    to; an `aclose()` here that closed it would break the rest of the application.
    """
    borrowed = httpx2.AsyncClient(
        transport=httpx2.MockTransport(lambda request: httpx2.Response(200, json={}))
    )
    client = ESCRouterClient(base_url="https://router.test/esc-rest", client=borrowed)

    await client.aclose()

    assert not borrowed.is_closed


async def test_an_owned_http_client_is_closed():
    client = ESCRouterClient(base_url="https://router.test/esc-rest")

    await client.aclose()

    assert client._client.is_closed


async def test_the_context_manager_closes_what_it_owns():
    async with ESCRouterClient(base_url="https://router.test/esc-rest") as client:
        inner = client._client

    assert inner.is_closed
