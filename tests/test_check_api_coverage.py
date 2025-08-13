from edutap.esc_router_api import api
from typing import Any
from typing import Dict

import httpx
import inspect
import json
import pathlib
import pytest


# URL zur OpenAPI-Spezifikation
ESC_API = "https://router.europeanstudentcard.eu/esc-rest/v3/api-docs/V2"
DATA_DIR = pathlib.Path(__file__).parent / "data"


def get_openapi_spec() -> bool:
    try:
        """Lädt die aktuelle OpenAPI-Spezifikation vom Server."""
        response = httpx.get(ESC_API)
        if response.status_code != 200:
            response.raise_for_status()
            raise httpx.HTTPError(
                f"Faild to fetch data from '{ESC_API}'."
                f"Status Code: {response.status_code}"
                f"Response: {response}"
            )
        data = json.loads(response.text)
        with open(DATA_DIR / "esc-router-v2.json", "w") as f:
            json.dump(data, f, indent=2, sort_keys=True)
            f.write("\n")

    except httpx.HTTPError as e:
        print(e)
        return False
    return True


def test_get_spec():
    assert get_openapi_spec()


@pytest.fixture(scope="session")
def load_spec():
    data: Dict[str, Any] = {}
    with open(DATA_DIR / "esc-router-v2.json") as file:
        data = json.load(file)
    return data


def get_openapi_operations(spec):
    """Extract all (method, path) from the OpenAPI specification."""
    operations = set()
    for path, methods in spec.get("paths", {}).items():
        for method in methods:
            operations.add((method.lower(), path))

    print("API endpoints:")
    for method, path in operations:
        print(f" * {method}: {path}")
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
            operations.add((obj.__http_method__, obj.__openapi_path__, obj.__name__))

    print("Our known endpoints:")
    for method, path, name in operations:
        print(f" * {method}: {path} - {name}")
    return operations


def test_all_openapi_operations_implemented(load_spec):
    """Prüft, ob alle API-Endpunkte implementiert sind."""
    spec_ops = get_openapi_operations(load_spec)
    impl_ops = get_implemented_operations(api)

    missing = spec_ops - impl_ops
    extra = impl_ops - spec_ops

    assert not missing, f"Fehlende API-Methoden: {sorted(missing)}"
    if extra:
        print(
            f"Warnung: Nicht in OpenAPI definierte Methoden gefunden: {sorted(extra)}"
        )
