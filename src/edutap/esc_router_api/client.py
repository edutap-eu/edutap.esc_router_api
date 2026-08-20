"""The ESC Router client.

One class holds the whole conversation with the router: how a request is addressed,
how the API key is attached, how a status code becomes an exception, and how a paged
endpoint is walked. Everything in :mod:`edutap.esc_router_api.api` is a thin call into
it.

The HTTP client is injected rather than created, so that a service which already keeps
a shared `httpx2.AsyncClient` -- a FastAPI application, most of the time -- reuses its
connection pool instead of opening a second one, and so that a test can hand in an
`httpx2.MockTransport` and never touch the network. Where no client is passed, one is
built and owned; :meth:`ESCRouterClient.aclose` then closes it and only then.
"""

import json
import logging
import threading
import uuid
from collections.abc import Mapping
from typing import Any
from typing import Literal
from typing import Self
from typing import TypeVar

import httpx2
from pydantic import BaseModel

from .exceptions import ESCRouterAuthenticationError
from .exceptions import ESCRouterConflict
from .exceptions import ESCRouterError
from .exceptions import ESCRouterGone
from .exceptions import ESCRouterNotFound
from .exceptions import ESCRouterPermissionError
from .exceptions import ESCRouterRequestError
from .exceptions import ESCRouterUnavailable
from .exceptions import ESCRouterValidationError
from .models import ApiErrorMessage
from .models import CardLiteView
from .models import CardStatusView
from .models import CardUpdateView
from .models import CardView
from .models import CsvOperation
from .models import CsvValidationError
from .models import PagedResourcesCardLiteView
from .models import PagedResourcesPersonLiteView
from .models import PersonLiteView
from .models import PersonUpdateView
from .models import PersonView
from .settings import Settings


__all__ = [
    "BASE_PATH",
    "ESCRouterClient",
    "close_default_client",
    "get_default_client",
    "set_default_client",
]

logger = logging.getLogger(__name__)

# No `logging.config.dictConfig()` anywhere in this package. This module used to run one
# at import time, which reconfigured the logging of whatever imported it -- including
# putting httpx and httpcore on DEBUG. A library takes a logger; it does not set up
# logging.

BASE_PATH = "/api/v2"

#: How many entries the router returns per page. The list endpoints default to ten and
#: do not honour a larger value, so walking a result set means walking it ten at a time.
PAGE_SIZE = 10

_PagedModel = TypeVar("_PagedModel", PagedResourcesPersonLiteView, PagedResourcesCardLiteView)


class ESCRouterClient:
    """Talks to one deployment of the ESC Router.

    Construct it from settings for the ordinary case::

        client = ESCRouterClient.from_settings()
        try:
            persons = await client.list_persons(size=0)
        finally:
            await client.aclose()

    or as a context manager, which is the same thing without the `finally`::

        async with ESCRouterClient.from_settings() as client:
            persons = await client.list_persons(size=0)
    """

    def __init__(
        self,
        *,
        base_url: str,
        api_key: str | None = None,
        timeout: float = 10.0,
        client: httpx2.AsyncClient | None = None,
        verify_https: bool = True,
    ) -> None:
        """Hold the connection settings, and the HTTP client if one was passed.

        :param base_url: The router root, including its `/esc-rest` path segment.
        :param api_key: Sent as `Authorization: Bearer …` on every call but the public
            card status endpoint.
        :param timeout: Seconds per request.
        :param client: An `httpx2.AsyncClient` to borrow. When omitted, one is built
            and owned by this instance.
        :param verify_https: Only ever false against a local mock.
        """
        self._base_url = base_url.rstrip("/")
        self._api_key = api_key
        self._timeout = timeout
        # Ownership decides what `aclose()` is allowed to do. Closing a client that was
        # handed in would take down the connection pool of the application that shared
        # it -- which is the failure mode that made the previous `atexit` hook here
        # dangerous as well as ineffective.
        self._owns_client = client is None
        self._client = client or httpx2.AsyncClient(
            http2=True,
            timeout=timeout,
            verify=verify_https,
        )

    @classmethod
    def from_settings(
        cls,
        settings: Settings | None = None,
        *,
        client: httpx2.AsyncClient | None = None,
    ) -> Self:
        """Build a client from `ESC_*` environment variables.

        :param settings: Read from the environment when omitted.
        :param client: An `httpx2.AsyncClient` to borrow, as in :meth:`__init__`.
        """
        settings = settings or Settings()
        return cls(
            base_url=settings.base_url,
            api_key=settings.api_key,
            timeout=settings.timeout,
            client=client,
            verify_https=settings.verify_https,
        )

    async def __aenter__(self) -> Self:
        """Enter the context; nothing to open, the client is already built."""
        return self

    async def __aexit__(self, *exc_info: object) -> None:
        """Close the HTTP client if this instance owns it."""
        await self.aclose()

    async def aclose(self) -> None:
        """Release the connection pool, but only if this instance created it.

        Safe to call more than once, and safe to call on a client that borrows an
        injected `httpx2.AsyncClient` -- it does nothing in that case.
        """
        if self._owns_client:
            await self._client.aclose()

    # --- Persons ------------------------------------------------------------------

    async def list_persons(
        self,
        *,
        sort: Literal["fullName", "identifier"] | None = None,
        direction: Literal["ASC", "DESC"] = "ASC",
        page: int = 0,
        size: int = 10,
        search: str | None = None,
    ) -> list[PersonLiteView]:
        """List persons, walking the router's pages as far as `size` requires.

        :param sort: Field to sort by.
        :param direction: Sort direction.
        :param page: The router page to start at, counted from zero.
        :param size: How many entries to return at most. **Zero means every entry**,
            which for a large institution is a great many requests -- see
            :meth:`_paginate`.
        :param search: Free text passed to the router unchanged.
        """
        return await self._paginate(
            f"{BASE_PATH}/persons",
            PagedResourcesPersonLiteView,
            sort=sort,
            direction=direction,
            page=page,
            size=size,
            search=search,
        )

    async def add_person(self, data: PersonUpdateView | Mapping[str, Any]) -> PersonView:
        """Register a person with the router.

        :raises ESCRouterConflict: The European Student Identifier is already taken.
            On a re-import this is the expected answer, not a failure.
        """
        payload = _as_model(data, PersonUpdateView)
        response = await self._request(
            "POST",
            f"{BASE_PATH}/persons",
            json_body=payload.model_dump(mode="json", exclude_none=True),
        )
        return PersonView.model_validate_json(response.text)

    async def get_person(self, esi: str) -> PersonView:
        """Retrieve one person by European Student Identifier."""
        response = await self._request("GET", f"{BASE_PATH}/persons/{esi}")
        return PersonView.model_validate_json(response.text)

    async def update_person(
        self, esi: str, data: PersonUpdateView | Mapping[str, Any]
    ) -> PersonView:
        """Replace one person's record."""
        payload = _as_model(data, PersonUpdateView)
        response = await self._request(
            "PUT",
            f"{BASE_PATH}/persons/{esi}",
            json_body=payload.model_dump(mode="json", exclude_none=True),
        )
        return PersonView.model_validate_json(response.text)

    async def delete_person(self, esi: str) -> None:
        """Remove one person.

        Returns nothing. The previous release returned `True` here, but the `False`
        branch was unreachable -- a failure had already raised -- so the boolean only
        ever said "no exception was thrown".
        """
        await self._request("DELETE", f"{BASE_PATH}/persons/{esi}")

    # --- Person pictures ----------------------------------------------------------
    #
    # These three take the organisation whose copy of the picture is meant. There is
    # one picture per person *per organisation*, which is why the identifier is in the
    # path and not optional. Earlier releases of this package interpolated the builtin
    # `id` into the URL instead of a parameter, so the requests went to a path
    # containing "<built-in function id>" and these operations never worked.

    async def get_person_image(self, organisation_id: str, esi: str) -> bytes:
        """Download a person's picture as stored for one organisation."""
        response = await self._request(
            "GET",
            f"{BASE_PATH}/organisations/{organisation_id}/person/{esi}/picture",
        )
        return response.content

    async def add_person_image(
        self,
        organisation_id: str,
        esi: str,
        image: bytes,
        *,
        filename: str = "picture.jpg",
        content_type: str = "image/jpeg",
        resize: bool = False,
    ) -> str:
        """Upload a person's picture.

        The router wants exactly 200x300 pixels. Pass `resize=True` to have it crop and
        scale whatever is sent; without that flag a differently sized image is refused.

        :returns: Whatever the router reports about the stored file -- a bare JSON
            string, so the text is returned as-is.
        """
        response = await self._request(
            "POST",
            f"{BASE_PATH}/organisations/{organisation_id}/person/{esi}/picture",
            params={"resize": resize},
            files={"file": (filename, image, content_type)},
        )
        return response.text

    async def delete_person_image(self, organisation_id: str, esi: str) -> None:
        """Remove a person's picture for one organisation."""
        await self._request(
            "DELETE",
            f"{BASE_PATH}/organisations/{organisation_id}/person/{esi}/picture",
        )

    # --- Cards --------------------------------------------------------------------

    async def list_cards(
        self,
        *,
        sort: str | None = None,
        direction: Literal["ASC", "DESC"] = "ASC",
        page: int = 0,
        size: int = 10,
        search: str | None = None,
    ) -> list[CardLiteView]:
        """List cards. Parameters as in :meth:`list_persons`."""
        return await self._paginate(
            f"{BASE_PATH}/cards",
            PagedResourcesCardLiteView,
            sort=sort,
            direction=direction,
            page=page,
            size=size,
            search=search,
        )

    async def add_card(self, data: CardUpdateView | Mapping[str, Any]) -> CardView:
        """Issue a card. Leave `cardNumber` unset to have the router assign one."""
        payload = _as_model(data, CardUpdateView)
        response = await self._request(
            "POST",
            f"{BASE_PATH}/cards",
            json_body=payload.model_dump(mode="json", exclude_none=True),
        )
        return CardView.model_validate_json(response.text)

    async def get_card(self, escn: str) -> CardView:
        """Retrieve one card by its European Student Card Number."""
        response = await self._request("GET", f"{BASE_PATH}/cards/{escn}")
        return CardView.model_validate_json(response.text)

    async def update_card(self, escn: str, data: CardUpdateView | Mapping[str, Any]) -> CardView:
        """Replace one card's record.

        Bringing an expired card back needs both a status of `ACTIVE` or `INACTIVE`
        and a new `expiresAt`; one without the other is rejected.
        """
        payload = _as_model(data, CardUpdateView)
        response = await self._request(
            "PUT",
            f"{BASE_PATH}/cards/{escn}",
            json_body=payload.model_dump(mode="json", exclude_none=True),
        )
        return CardView.model_validate_json(response.text)

    async def delete_card(self, escn: str) -> None:
        """Remove one card. Returns nothing, as :meth:`delete_person` does."""
        await self._request("DELETE", f"{BASE_PATH}/cards/{escn}")

    async def get_card_status(self, escn: str) -> CardStatusView:
        """Look up a card's status.

        This is the endpoint behind the QR code on a card, and the only one the router
        serves without an API key.
        """
        response = await self._request(
            "GET", f"{BASE_PATH}/cards/{escn}/status", authenticated=False
        )
        return CardStatusView.model_validate_json(response.text)

    async def generate_card_numbers(
        self,
        pic: str,
        *,
        prefix: int = 1,
        number_of_escn: int = 10,
    ) -> list[uuid.UUID]:
        """Ask the router to reserve card numbers.

        :param pic: The institution's Participant Identification Code, nine digits.
        :param prefix: Three digits distinguishing several servers of one institution.
        :param number_of_escn: How many to reserve, at most 100 per call.
        :raises ValueError: `number_of_escn` outside 0..100. Checked here rather than
            left to the router, which answers 500 rather than 400 for this.
        """
        if not 0 <= number_of_escn <= 100:
            raise ValueError("number_of_escn must be between 0 and 100")
        response = await self._request(
            "GET",
            f"{BASE_PATH}/cards/generate-escn",
            params={"pic": pic, "prefix": prefix, "numberOfESCN": number_of_escn},
        )
        return [uuid.UUID(escn) for escn in json.loads(response.text)]

    async def get_card_qr_code(
        self,
        escn: str,
        *,
        orientation: Literal["vertical", "horizontal"] = "horizontal",
        colours: Literal["normal", "inverted"] = "normal",
        size: Literal["XS", "S", "M"] = "S",
        accept: Literal["SVG", "TEXT", "image/svg+xml", "text/plain"] = "SVG",
    ) -> bytes:
        """Render the QR code that points at this card's public status page.

        :param accept: `SVG` for the drawing, `TEXT` for a base64 encoding of it. The
            two MIME types are accepted as synonyms for convenience.
        :returns: The raw body. It is bytes in both cases -- decode it yourself for
            `TEXT`, because the router does not always send a charset.
        """
        media_type = {
            "SVG": "image/svg+xml",
            "image/svg+xml": "image/svg+xml",
            "TEXT": "text/plain",
            "text/plain": "text/plain",
        }[accept]
        response = await self._request(
            "GET",
            f"{BASE_PATH}/cards/{escn}/qr",
            params={"orientation": orientation, "colours": colours, "size": size},
            headers={"Accept": media_type},
        )
        return response.content

    # --- Bulk card import ---------------------------------------------------------

    async def get_csv_config(self) -> dict[str, int]:
        """Retrieve the column layout the router expects in a card import CSV.

        The mapping is column name to zero-based position. It is worth reading rather
        than hard-coding: the router has reordered these columns before.
        """
        response = await self._request("GET", f"{BASE_PATH}/cards/csv-config")
        return json.loads(response.text)

    async def validate_csv(
        self,
        csv_file: bytes,
        *,
        operation: CsvOperation,
        filename: str = "cards.csv",
    ) -> list[CsvValidationError]:
        """Have the router check a card import file without importing it.

        An empty list means every row passed. This is a dry run in both directions:
        nothing is written, and nothing is reserved either.
        """
        response = await self._request(
            "POST",
            f"{BASE_PATH}/cards/validate-csv",
            params={"operation": operation},
            files={"file": (filename, csv_file, "text/csv")},
        )
        return [CsvValidationError.model_validate(row) for row in json.loads(response.text)]

    # --- Plumbing -----------------------------------------------------------------

    async def _paginate(
        self,
        path: str,
        model: type[_PagedModel],
        *,
        sort: str | None,
        direction: str,
        page: int,
        size: int,
        search: str | None,
    ) -> list[Any]:
        """Walk a paged endpoint and return the entries.

        `size` is a ceiling on entries, not a page width -- the router's page width is
        fixed at :data:`PAGE_SIZE` and it ignores a larger `size`. `size=0` means every
        entry there is.

        Three separate conditions end the walk, and all three are needed: the router
        reporting `empty`, a short page, and the page counter reaching `totalPages`.
        The version of this loop that shipped before had none of them working together
        and could spin.
        """
        collected: list[Any] = []
        current = page

        while True:
            remaining = None if size == 0 else size - len(collected)
            if remaining is not None and remaining <= 0:
                break

            request_size = PAGE_SIZE if remaining is None else min(PAGE_SIZE, remaining)
            params: dict[str, Any] = {
                "page": current,
                "size": request_size,
                "direction": direction,
            }
            if sort:
                params["sort"] = sort
            if search:
                params["search"] = search

            response = await self._request("GET", path, params=params)
            payload = model.model_validate_json(response.text)
            items = payload.content or []
            collected.extend(items)
            logger.debug(
                "%s page %s returned %s entries (%s collected)",
                path,
                current,
                len(items),
                len(collected),
            )

            if payload.empty or not items or len(items) < request_size:
                break
            total_pages = payload.page.totalPages if payload.page else None
            if total_pages is not None and current + 1 >= total_pages:
                break
            current += 1

        return collected

    async def _request(
        self,
        method: str,
        path: str,
        *,
        params: Mapping[str, Any] | None = None,
        json_body: Any = None,
        headers: Mapping[str, str] | None = None,
        files: Any = None,
        authenticated: bool = True,
    ) -> httpx2.Response:
        """Make one request and turn anything that is not a success into an exception.

        This is the only place in the package that knows what a status code means, so
        the mapping is stated once instead of sixteen times.
        """
        request_headers: dict[str, str] = dict(headers or {})
        if authenticated and self._api_key:
            # The API key rides in `Authorization`, and it is set per request rather
            # than on the client: an injected client may be shared with calls to other
            # hosts, and a default header would send the router's key to all of them.
            request_headers["Authorization"] = f"Bearer {self._api_key}"

        url = f"{self._base_url}{path}"
        try:
            response = await self._client.request(
                method,
                url,
                params=params,
                json=json_body,
                files=files,
                headers=request_headers,
                timeout=self._timeout,
            )
        except httpx2.HTTPError as exc:
            raise ESCRouterUnavailable(f"{method} {path} did not answer: {exc}") from exc

        if response.status_code < 300:
            return response
        raise _exception_for(method, path, response)


def _as_model[M: BaseModel](data: BaseModel | Mapping[str, Any], model: type[M]) -> M:
    """Accept either a model or a plain mapping, and validate the mapping.

    `data` is deliberately not typed `M`: binding the type variable to the argument as
    well as to `model` makes it resolve to the union at every call site, and the
    checker then rejects what is plainly correct. `model` alone determines `M`.
    """
    if isinstance(data, model):
        return data
    return model.model_validate(data)


def _exception_for(method: str, path: str, response: httpx2.Response) -> ESCRouterError:
    """Build the exception that belongs to a failed response.

    The router answers with an `ApiErrorMessage` where it can, but not always -- the
    picture endpoints reply `*/*` and a gateway in front of it may answer with HTML.
    A body that will not parse is therefore not itself an error.
    """
    error: ApiErrorMessage | None = None
    try:
        error = ApiErrorMessage.model_validate_json(response.text)
    except ValueError:
        logger.debug(
            "no ApiErrorMessage in the %s body for %s %s", response.status_code, method, path
        )

    status = response.status_code
    detail = f"{method} {path} -> {status}"
    if error and error.message:
        detail = f"{detail}: {error.message}"

    exception_type: type[ESCRouterError]
    match status:
        case 400:
            exception_type = ESCRouterRequestError
        case 401:
            exception_type = ESCRouterAuthenticationError
        case 403:
            exception_type = ESCRouterPermissionError
        case 404:
            exception_type = ESCRouterNotFound
        case 409:
            exception_type = ESCRouterConflict
        case 410:
            exception_type = ESCRouterGone
        case _ if 300 <= status < 400:
            # Redirects are not followed. The client sets `Authorization` per request,
            # so httpx2 would not strip it on a cross-host redirect the way it does for
            # a header set on the client -- following one would hand the API key to
            # whatever the router pointed at.
            exception_type = ESCRouterUnavailable
            detail = f"{detail}: unexpected redirect to {response.headers.get('location')!r}"
        case _ if status >= 500:
            exception_type = ESCRouterUnavailable
        case _:
            exception_type = ESCRouterValidationError

    logger.error(detail)
    return exception_type(detail, status_code=status, error=error)


# --- The default client, for the module-level API ---------------------------------
#
# A process-wide client built from the environment, so that `from …api import
# get_person` works with no setup. It replaces a thread-local plus an `atexit` hook
# that called `aclose()` without awaiting it -- the coroutine was never run, and a new
# hook was registered on every client creation.

_default_client: ESCRouterClient | None = None
_default_client_lock = threading.Lock()


def get_default_client() -> ESCRouterClient:
    """Return the process-wide client, building it from `ESC_*` on first use."""
    global _default_client
    if _default_client is None:
        with _default_client_lock:
            if _default_client is None:
                _default_client = ESCRouterClient.from_settings()
    return _default_client


def set_default_client(client: ESCRouterClient | None) -> None:
    """Replace the process-wide client.

    Intended for an application that builds its own client at startup, and for tests.
    Passing `None` drops it, so the next call rebuilds from the environment. The
    previous client is *not* closed -- whoever set it decides that.
    """
    global _default_client
    with _default_client_lock:
        _default_client = client


async def close_default_client() -> None:
    """Close the process-wide client, if one was ever built."""
    global _default_client
    with _default_client_lock:
        client, _default_client = _default_client, None
    if client is not None:
        await client.aclose()
