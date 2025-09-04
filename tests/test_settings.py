from edutap.esc_router_api.session import Settings

import pytest


def test_settings():
    settings = Settings()
    assert settings is not None
    assert settings.environment == "development"
    assert settings.api_key is not None
    print(settings.model_dump_json(indent=2))