"""Shared fixtures.

The unit suite never opens a socket. Every test drives an `ESCRouterClient` whose
`httpx2.AsyncClient` is wired to an `httpx2.MockTransport`, so what is exercised is the
real client -- its URL building, its headers, its status mapping, its pagination -- with
only the wire replaced. That is the difference from mocking the client itself, which
would test the test.
"""

import json
import pathlib
from collections.abc import Callable

import httpx2
import pytest

from edutap.esc_router_api.client import ESCRouterClient


DATA_DIR = pathlib.Path(__file__).parent / "data"

#: Any absolute URL will do -- MockTransport never resolves it. A `.test` host is used
#: so that a bug which bypasses the transport fails to connect instead of reaching a
#: real router.
BASE_URL = "https://router.test/esc-rest"

API_KEY = "test-api-key"


@pytest.fixture(scope="session")
def anyio_backend() -> str:
    """Run the async tests on asyncio only; there is no trio-specific behaviour here."""
    return "asyncio"


@pytest.fixture
def spec() -> dict:
    """The router's OpenAPI document, as captured by `make refresh-spec`."""
    return json.loads((DATA_DIR / "esc-router-v2.json").read_text())


class FakeRouter:
    """A stand-in for the router that answers from a script and records what it was asked.

    Responses are queued per `(method, path)`. A path is matched without its query
    string, because the query is what several tests want to assert *about* rather than
    to address by. When a queue holds one entry it is reused for every further call,
    which keeps the pagination tests from having to enumerate identical pages.
    """

    def __init__(self) -> None:
        """Start with no routes and no history."""
        self._routes: dict[tuple[str, str], list[httpx2.Response]] = {}
        self.requests: list[httpx2.Request] = []

    def add(
        self,
        method: str,
        path: str,
        *,
        status: int = 200,
        json_body: object = None,
        content: bytes | None = None,
        headers: dict[str, str] | None = None,
    ) -> "FakeRouter":
        """Queue one response. Returns self, so calls chain."""
        response = httpx2.Response(
            status,
            json=json_body,
            content=content,
            headers=headers,
        )
        self._routes.setdefault((method.upper(), path), []).append(response)
        return self

    def handler(self, request: httpx2.Request) -> httpx2.Response:
        """Answer one request, recording it first."""
        self.requests.append(request)
        key = (request.method, request.url.path)
        queue = self._routes.get(key)
        if not queue:
            raise AssertionError(f"FakeRouter has no response queued for {key}")
        return queue.pop(0) if len(queue) > 1 else queue[0]

    @property
    def last_request(self) -> httpx2.Request:
        """The most recent request, for asserting on headers and query parameters."""
        return self.requests[-1]


@pytest.fixture
def router() -> FakeRouter:
    """An empty scripted router. Queue responses on it before calling the client."""
    return FakeRouter()


@pytest.fixture
def make_client(router: FakeRouter) -> Callable[..., ESCRouterClient]:
    """Build an `ESCRouterClient` talking to the scripted router.

    The transport is injected as an `httpx2.AsyncClient`, which also exercises the
    borrowed-client path: `aclose()` must leave a client it did not create alone.
    """

    def factory(*, api_key: str | None = API_KEY) -> ESCRouterClient:
        transport = httpx2.MockTransport(router.handler)
        return ESCRouterClient(
            base_url=BASE_URL,
            api_key=api_key,
            client=httpx2.AsyncClient(transport=transport),
        )

    return factory


@pytest.fixture
def client(make_client: Callable[..., ESCRouterClient]) -> ESCRouterClient:
    """The common case: an authenticated client against the scripted router."""
    return make_client()
