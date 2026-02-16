from edutap.esc_router_api import api
from typing import Any
from typing import Dict

import httpx
import inspect
import json
import pathlib
import pytest


# URL zur OpenAPI-Spezifikation
# ESC_API_V3 = "https://dev.europeanstudentcard.eu/esc-rest/v3/api-docs/V2"
# ESC_API_V2 = "https://router.europeanstudentcard.eu/esc-rest/v3/api-docs/V2"
# ESC_API_V1 = "https://router.europeanstudentcard.eu/esc-rest/v3/api-docs/V1"
ESC_API_V2 = "https://sandbox.europeanstudentcard.eu/esc-rest/v3/api-docs/V2"
ESC_API_V1 = "https://sandbox.europeanstudentcard.eu/esc-rest/v3/api-docs/V1"
DATA_DIR = pathlib.Path(__file__).parent / "data"


class Operation:
    def __init__(self, method: str, path: str, operationId: str):
        self.method = method
        self.path = path
        self.operationId = operationId

    def __hash__(self):
        return hash((self.method, self.path, self.operationId))

    def __eq__(self, other):
        if not isinstance(other, Operation):
            return NotImplemented
        return (self.method, self.path, self.operationId) == (other.method, other.path, other.operationId)

    def __lt__(self, other):
        if not isinstance(other, Operation):
            return NotImplemented
        return (self.method, self.path, self.operationId) < (other.method, other.path, other.operationId)

    def __repr__(self):
        return f"Operation(method={self.method}, path={self.path}, operationId={self.operationId})"


def get_openapi_spec(url, version) -> bool:
    try:
        """Lädt die aktuelle OpenAPI-Spezifikation vom Server."""
        response = httpx.get(url)
        if response.status_code != 200:
            response.raise_for_status()
            raise httpx.HTTPError(f"Failed to fetch data from '{url}'. Status Code: {response.status_code} Response: {response}")
        data = json.loads(response.text)
        with open(DATA_DIR / f"esc-router-{version}.json", "w") as f:
            json.dump(data, f, indent=2, sort_keys=True)
            f.write("\n")

    except httpx.HTTPError as e:
        print(e)
        return False
    return True


def test_get_spec():
    # assert get_openapi_spec(ESC_API_V3, "v3")
    assert get_openapi_spec(ESC_API_V2, "v2")
    assert get_openapi_spec(ESC_API_V1, "v1")


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
            operations.add(Operation(method=method.upper(), path=path, operationId=details.get("operationId")))

    print("API endpoints:")
    for op in operations:
        print(f" * {op.method}: {op.path} - ({op.operationId})")
    return operations


def get_implemented_operations(api_module):
    """Find all functions in the API module that are decorated with @openapi_method."""
    operations = set()
    for _, obj in inspect.getmembers(api_module):
        if callable(obj) and hasattr(obj, "__http_method__") and hasattr(obj, "__openapi_path__"):
            operations.add(
                Operation(
                    method=obj.__http_method__,
                    path=obj.__openapi_path__,
                    # name=obj.__name__,
                    operationId=obj.__openapi_operation_id__,
                )
            )

    print("Our known endpoints:")
    for op in operations:
        print(f" * {op.method}: {op.path} - ({op.operationId})")
    return operations


@pytest.mark.parametrize("version", [2, 3])
def test_all_openapi_operations_implemented(version):
    """Check, if all OpenAPI operations are implemented."""
    spec_ops = get_openapi_operations(load_spec(version=version))
    impl_ops = get_implemented_operations(api_module=api)

    missing = spec_ops - impl_ops
    extra = impl_ops - spec_ops

    if missing:
        missing_list = sorted(missing)
        print(f"Missing API methods found: ")
        for op in missing_list:
            print(f" * {op.method}: {op.path} - ({op.operationId})")

    assert not missing, f"Missing API methods: {sorted(missing)}"
    if extra:
        print(f"Warning: Not defined in OpenAPI methods found: {sorted(extra)}")
