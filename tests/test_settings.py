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


def test_the_api_key_is_read_from_a_mounted_file(tmp_path):
    """A Docker secret, not an environment variable.

    `docker service inspect` prints environment variables to everyone allowed to run
    it, and an error tracker collects them out of frame locals. An API key is exactly
    the kind of value that must not travel that way.

    THE FILE NAME CARRIES THE PREFIX: `ESC_API_KEY`, not `api_key`. A secret mounted
    under the bare field name is silently ignored.
    """
    (tmp_path / "ESC_API_KEY").write_text("from-the-file")

    settings = Settings(_env_file=None, _secrets_dir=str(tmp_path))

    assert settings.api_key == "from-the-file"


def test_the_secrets_dir_is_declared():
    """The counter-check, and the failure it guards against.

    Until 2026-08-28 this class declared no `secrets_dir` at all, so a mounted
    `ESC_API_KEY` was never read -- silently, because nothing distinguishes "the file
    was not read" from "no key was configured". `api_key` simply stayed `None`.

    A behavioural test cannot catch that: with no `secrets_dir` there is no file that
    gets read wrongly, only one that is never read. So this asserts the DECLARATION.

    The same gap cost two deployments in the eduTAP estate on 2026-08-27, in a
    different package, for exactly the same reason.
    """
    assert Settings.model_config["secrets_dir"] == "/run/secrets"


def test_a_missing_secrets_dir_is_survivable(monkeypatch):
    """A development machine has no /run/secrets, and must not care.

    pydantic-settings emits a UserWarning and falls back to the environment. If that
    ever became an error, every developer's first import would fail.
    """
    monkeypatch.setenv("ESC_API_KEY", "from-the-environment")

    settings = Settings(_env_file=None, _secrets_dir="/nonexistent-on-purpose")

    assert settings.api_key == "from-the-environment"


def test_the_environment_still_wins_over_nothing(monkeypatch):
    """No file, no `secrets_dir` hit: the variable is still read as before."""
    monkeypatch.setenv("ESC_API_KEY", "plain")

    assert Settings(_env_file=None).api_key == "plain"
