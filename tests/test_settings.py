"""Configuration resolution.

Every test builds `Settings` with explicit keyword arguments or a monkeypatched
environment, and none of them reads the developer's `.env`. The old test asserted
`settings.api_key is not None`, which passed on a machine with a key configured and
failed everywhere else -- including CI.
"""

import pytest

from edutap.esc_router_api.settings import BASE_URLS
from edutap.esc_router_api.settings import Settings


@pytest.fixture(autouse=True)
def _no_ambient_configuration(monkeypatch, tmp_path):
    """Keep the developer's environment and `.env` out of these assertions."""
    for name in ("ESC_API_KEY", "ESC_ENVIRONMENT", "ESC_BASE_URL", "ESC_TIMEOUT"):
        monkeypatch.delenv(name, raising=False)
    monkeypatch.chdir(tmp_path)


def test_the_defaults_point_at_the_sandbox():
    """Development is the default, so a forgotten `ESC_ENVIRONMENT` cannot write to production."""
    settings = Settings()

    assert settings.environment == "development"
    assert settings.base_url == BASE_URLS["development"]
    assert "sandbox" in settings.base_url


@pytest.mark.parametrize("environment", sorted(BASE_URLS))
def test_the_base_url_follows_the_environment(monkeypatch, environment):
    monkeypatch.setenv("ESC_ENVIRONMENT", environment)

    assert Settings().base_url == BASE_URLS[environment]


def test_an_explicit_base_url_wins(monkeypatch):
    """So that a local mock or an unlisted deployment needs no code change."""
    monkeypatch.setenv("ESC_ENVIRONMENT", "production")
    monkeypatch.setenv("ESC_BASE_URL", "http://localhost:8080/esc-rest/")

    assert Settings().base_url == "http://localhost:8080/esc-rest/"


def test_the_resolved_url_is_part_of_the_model():
    """It has to show up in a dump, which is where somebody looks after a wrong call."""
    assert "base_url" in Settings().model_dump()


def test_the_environment_prefix_is_esc(monkeypatch):
    monkeypatch.setenv("ESC_API_KEY", "from-the-environment")

    assert Settings().api_key == "from-the-environment"


def test_a_dot_env_file_is_read(monkeypatch, tmp_path):
    (tmp_path / ".env").write_text("ESC_API_KEY=from-the-file\n")
    monkeypatch.chdir(tmp_path)

    assert Settings().api_key == "from-the-file"


def test_a_non_positive_timeout_is_refused():
    """Zero means "no timeout" to some clients and "give up now" to others."""
    with pytest.raises(ValueError, match="timeout"):
        Settings(timeout=0)


def test_an_unknown_environment_is_refused():
    with pytest.raises(ValueError, match="environment"):
        Settings(environment="staging")
