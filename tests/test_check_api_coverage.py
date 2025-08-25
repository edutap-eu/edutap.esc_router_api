# from edutap.esc_router_api import api_v1
from edutap.esc_router_api import api_v2
from typing import Any
from typing import Dict

import httpx
import inspect
import json
import pathlib
import pytest


# URL zur OpenAPI-Spezifikation
ESC_API_V2 = "https://router.europeanstudentcard.eu/esc-rest/v3/api-docs/V2"
ESC_API_V1 = "https://router.europeanstudentcard.eu/esc-rest/v3/api-docs/V1"
DATA_DIR = pathlib.Path(__file__).parent / "data"


def get_openapi_spec(url, version) -> bool:
    try:
        """Lädt die aktuelle OpenAPI-Spezifikation vom Server."""
        response = httpx.get(url)
        if response.status_code != 200:
            response.raise_for_status()
            raise httpx.HTTPError(
                f"Failed to fetch data from '{url}'."
                f"Status Code: {response.status_code}"
                f"Response: {response}"
            )
        data = json.loads(response.text)
        with open(DATA_DIR / f"esc-router-{version}.json", "w") as f:
            json.dump(data, f, indent=2, sort_keys=True)
            f.write("\n")

    except httpx.HTTPError as e:
        print(e)
        return False
    return True


def test_get_spec():
    assert get_openapi_spec(ESC_API_V2, "v2")
    assert get_openapi_spec(ESC_API_V1, "v1")


@pytest.fixture(scope="session")
def load_spec(version: int = 2):
    data: Dict[str, Any] = {}
    with open(DATA_DIR / f"esc-router-v{version}.json") as file:
        data = json.load(file)
    return data


def get_openapi_operations(spec):
    """Extract all (method, path) from the OpenAPI specification."""
    operations = set()
    for path, methods in spec.get("paths", {}).items():
        for method, details in methods.items():
            print(details)
            operations.add((method.lower(), path, details.get("operationId")))

    print("API endpoints:")
    for method, path, operation_id in operations:
        print(f" * {method}: {path} - {operation_id}")
    return operations


def get_implemented_operations(api_module):
    """Find all functions in the API module that are decorated with @openapi_method."""
    operations = set()
    for _, obj in inspect.getmembers(api_module):
        if (
            callable(obj)
            and hasattr(obj, "__http_method__")
            and hasattr(obj, "__openapi_path__")
        ):
            operations.add(
                (
                    obj.__http_method__,
                    obj.__openapi_path__,
                    obj.__name__,
                    obj.__openapi_operation_id__,
                )
            )

    print("Our known endpoints:")
    for method, path, name, operationId in operations:
        print(f" * {method}: {path} - {name} ({operationId})")
    return operations


# def test_all_v1_openapi_operations_implemented(load_spec):
#     """Check, if all OpenAPI operations are implemented."""
#     spec_ops = get_openapi_operations(load_spec(1))
#     impl_ops = get_implemented_operations(api_v1)

#     missing = spec_ops - impl_ops
#     extra = impl_ops - spec_ops

#     assert not missing, f"Missing API methods: {sorted(missing)}"
#     if extra:
#         print(f"Warning: Not defined in OpenAPI methods found: {sorted(extra)}")


def test_all_v2_openapi_operations_implemented(load_spec):
    """Check, if all OpenAPI operations are implemented."""
    spec_ops = get_openapi_operations(load_spec)
    impl_ops = get_implemented_operations(api_v2)

    missing = spec_ops - impl_ops
    extra = impl_ops - spec_ops

    assert not missing, f"Missing API methods: {sorted(missing)}"
    if extra:
        print(f"Warning: Not defined in OpenAPI methods found: {sorted(extra)}")
