"""Fixtures for the tests that talk to a real ESC Router.

These do not run under a plain `pytest`. `pytest-explicit` holds the `integration`
marker back until it is asked for by name, so `make test-local` stays offline and CI
never depends on a router being up. Run them with `make test-integration`.

Two guards stand between these tests and a bad afternoon:

* **`ESC_API_KEY` must be set**, otherwise they skip rather than fail. A missing key is
  a machine that was never configured for this, not a defect.
* **`ESC_ENVIRONMENT` must not be `production`.** Several of these create and delete
  records. Against the production router that is real data belonging to real students,
  and no test is worth that.
"""

import os

import pytest

from edutap.esc_router_api.client import ESCRouterClient
from edutap.esc_router_api.settings import Settings


pytestmark = pytest.mark.integration

#: The LMU's Participant Identification Code on the sandbox.
PIC = "999978433"


@pytest.fixture(scope="session")
def settings() -> Settings:
    """Settings for the router under test, or a skip if none are configured."""
    resolved = Settings()
    if not resolved.api_key:
        pytest.skip("ESC_API_KEY is not set -- see docs/howto/run-the-integration-tests.md")
    if resolved.environment == "production":
        pytest.skip(
            "refusing to run the integration tests against production: they create and "
            "delete records. Unset ESC_ENVIRONMENT or set it to development."
        )
    return resolved


@pytest.fixture
async def client(settings: Settings):
    """A client against the sandbox router, closed when the test ends."""
    async with ESCRouterClient.from_settings(settings) as router_client:
        yield router_client


@pytest.fixture
def destructive_allowed() -> bool:
    """Whether the tests that delete records may run.

    Off unless `ESC_ALLOW_DESTRUCTIVE_TESTS=1` is set. Emptying the sandbox is
    occasionally what you want and never what you want by accident -- and the sandbox is
    shared, so somebody else's fixtures are in there too.
    """
    return os.environ.get("ESC_ALLOW_DESTRUCTIVE_TESTS") == "1"
