"""Compare the module-level API against the router's OpenAPI document.

The previous version of this file fetched three specifications over the network *and
overwrote the checked-in fixtures with what it got* -- a unit test that needed the
internet and rewrote its own inputs, so a run against a router mid-deployment silently
changed what every later run compared against. Fetching now lives in `make
refresh-spec`, where the result lands in a diff somebody reads.
"""

import inspect
from typing import NamedTuple

from edutap.esc_router_api import api


class Operation(NamedTuple):
    """One router operation, by the three things that identify it."""

    method: str
    path: str
    operation_id: str | None


def operations_in_spec(spec: dict) -> set[Operation]:
    """Every operation the router publishes."""
    return {
        Operation(method.upper(), path, details.get("operationId"))
        for path, methods in spec["paths"].items()
        for method, details in methods.items()
        if method in {"get", "post", "put", "delete", "patch"}
    }


def operations_implemented() -> set[Operation]:
    """Every operation the `api` module claims, via its `openapi_method` decorations."""
    return {
        Operation(obj.__http_method__, obj.__openapi_path__, obj.__openapi_operation_id__)
        for _, obj in inspect.getmembers(api)
        if callable(obj) and hasattr(obj, "__http_method__")
    }


def test_every_operation_is_implemented(spec: dict) -> None:
    missing = operations_in_spec(spec) - operations_implemented()
    assert not missing, f"router operations with no function: {sorted(missing)}"


def test_no_function_outlives_its_operation(spec: dict) -> None:
    """A function for an operation the router withdrew is a call that 404s.

    `POST /api/v2/cards/issue/{escn}/{kid}` was implemented here after it disappeared
    from the specification, which is how this assertion came to exist.
    """
    extra = operations_implemented() - operations_in_spec(spec)
    assert not extra, f"functions with no router operation: {sorted(extra)}"


def test_operation_ids_are_unique() -> None:
    """Two functions claiming one operation would make the set comparison lie."""
    ids = [op.operation_id for op in operations_implemented()]
    assert len(ids) == len(set(ids))
