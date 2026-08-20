"""How the client walks a paged endpoint.

The loop this replaces had a condition that was a tautology, no use of the page
metadata, and no agreement between its two exit tests -- so `size=0` could not reliably
end and a partial last page was handled by accident. These are the cases that pinned
the behaviour down.
"""

import pytest

from edutap.esc_router_api.client import PAGE_SIZE


pytestmark = pytest.mark.anyio

PERSONS_PATH = "/esc-rest/api/v2/persons"


def page(identifiers: list[str], *, total_pages: int, empty: bool = False) -> dict:
    """One `PagedResourcesPersonLiteView` body."""
    return {
        "content": [{"identifier": identifier} for identifier in identifiers],
        "empty": empty,
        "page": {"size": PAGE_SIZE, "totalPages": total_pages},
    }


def identifiers(count: int, offset: int = 0) -> list[str]:
    return [f"urn:schac:personalUniqueCode:int:esi:lmu.de:{offset + n:08d}" for n in range(count)]


async def test_a_single_short_page_ends_the_walk(router, client):
    router.add("GET", PERSONS_PATH, json_body=page(identifiers(3), total_pages=1))

    persons = await client.list_persons(size=10)

    assert len(persons) == 3
    assert len(router.requests) == 1


async def test_size_zero_walks_every_page(router, client):
    """`size=0` means all of them, and the page metadata is what says when to stop."""
    router.add("GET", PERSONS_PATH, json_body=page(identifiers(PAGE_SIZE, 0), total_pages=3))
    router.add("GET", PERSONS_PATH, json_body=page(identifiers(PAGE_SIZE, 10), total_pages=3))
    router.add("GET", PERSONS_PATH, json_body=page(identifiers(PAGE_SIZE, 20), total_pages=3))

    persons = await client.list_persons(size=0)

    assert len(persons) == 30
    assert len(router.requests) == 3
    assert [request.url.params["page"] for request in router.requests] == ["0", "1", "2"]


async def test_size_larger_than_a_page_asks_for_as_many_as_are_left(router, client):
    """The last request asks for the remainder, not for another full page.

    Requesting 25 means three calls of 10, 10 and 5 -- not three of 10 followed by
    trimming, which would make the router assemble a page nobody reads.
    """
    router.add("GET", PERSONS_PATH, json_body=page(identifiers(PAGE_SIZE, 0), total_pages=9))
    router.add("GET", PERSONS_PATH, json_body=page(identifiers(PAGE_SIZE, 10), total_pages=9))
    router.add("GET", PERSONS_PATH, json_body=page(identifiers(5, 20), total_pages=9))

    persons = await client.list_persons(size=25)

    assert len(persons) == 25
    assert [request.url.params["size"] for request in router.requests] == ["10", "10", "5"]


async def test_size_smaller_than_a_page_makes_one_request(router, client):
    router.add("GET", PERSONS_PATH, json_body=page(identifiers(3), total_pages=9))

    persons = await client.list_persons(size=3)

    assert len(persons) == 3
    assert len(router.requests) == 1
    assert router.last_request.url.params["size"] == "3"


async def test_an_empty_first_page_returns_nothing(router, client):
    router.add("GET", PERSONS_PATH, json_body=page([], total_pages=0, empty=True))

    assert await client.list_persons(size=0) == []
    assert len(router.requests) == 1


async def test_the_walk_stops_at_total_pages_even_on_full_pages(router, client):
    """The safety net.

    A router that keeps answering with a full page and never sets `empty` would
    otherwise be walked forever. `totalPages` ends it.
    """
    router.add("GET", PERSONS_PATH, json_body=page(identifiers(PAGE_SIZE), total_pages=2))

    persons = await client.list_persons(size=0)

    assert len(persons) == 20
    assert len(router.requests) == 2


async def test_the_start_page_is_honoured(router, client):
    router.add("GET", PERSONS_PATH, json_body=page(identifiers(4), total_pages=9))

    await client.list_persons(page=7, size=10)

    assert router.last_request.url.params["page"] == "7"


async def test_optional_query_parameters_are_only_sent_when_given(router, client):
    router.add("GET", PERSONS_PATH, json_body=page(identifiers(1), total_pages=1))

    await client.list_persons(size=1)

    params = router.last_request.url.params
    assert "sort" not in params
    assert "search" not in params
    assert params["direction"] == "ASC"


async def test_sort_and_search_reach_the_router(router, client):
    router.add("GET", PERSONS_PATH, json_body=page(identifiers(1), total_pages=1))

    await client.list_persons(size=1, sort="identifier", direction="DESC", search="Mans")

    params = router.last_request.url.params
    assert params["sort"] == "identifier"
    assert params["direction"] == "DESC"
    assert params["search"] == "Mans"


async def test_cards_walk_the_same_way(router, client):
    router.add(
        "GET",
        "/esc-rest/api/v2/cards",
        json_body={
            "content": [{"cardNumber": f"card-{n}"} for n in range(PAGE_SIZE)],
            "empty": False,
            "page": {"totalPages": 2},
        },
    )

    cards = await client.list_cards(size=0)

    assert len(cards) == 20
