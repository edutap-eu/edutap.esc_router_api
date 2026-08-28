"""Configuration, read from the environment.

Everything is prefixed `ESC_`, so `ESC_API_KEY` and `ESC_ENVIRONMENT` configure a
deployment without a line of code. A `.env` file in the working directory is read too,
which is what makes the integration tests runnable without exporting a key by hand.

`load_dotenv()` used to be called at import time in this package. It is not any more:
a library that reads `.env` on import writes into the environment of whatever imports
it, and pydantic-settings already does the same job scoped to this class.
"""

from typing import Literal

from pydantic import Field
from pydantic import model_validator
from pydantic_settings import BaseSettings
from pydantic_settings import SettingsConfigDict


__all__ = ["Settings"]

#: The router's own deployments, keyed by ``ESC_ENVIRONMENT``. Production answers 403 to
#: any address that is not whitelisted, so a misconfigured environment shows up as an
#: authorisation failure rather than as a connection error -- worth knowing when reading
#: a traceback.
BASE_URLS: dict[str, str] = {
    "development": "https://sandbox.europeanstudentcard.eu/esc-rest/",
    "testing": "https://sandbox.europeanstudentcard.eu/esc-rest/",
    "production": "https://router.europeanstudentcard.eu/esc-rest/",
}


class Settings(BaseSettings):
    """Settings for the ESC Router client.

    Any field can be overridden by the environment variable of the same name, prefixed
    `ESC_`. For how the resolution order works, see
    https://pydantic.dev/docs/validation/latest/concepts/pydantic_settings/
    """

    #: `secrets_dir` is what lets the API key arrive as a mounted file rather than an
    #: environment variable. `docker service inspect` prints environment variables to
    #: everyone allowed to run it, and an error tracker collects them out of frame
    #: locals -- an API key is exactly the kind of value that must not travel that way.
    #:
    #: pydantic-settings HAS NO `_FILE` CONVENTION. It reads a secret file only where a
    #: `secrets_dir` says to look, and the name it looks for carries the prefix:
    #: `/run/secrets/ESC_API_KEY`, not `.../api_key`. A secret mounted under the bare
    #: field name is silently ignored -- silently, which is the whole problem: nothing
    #: distinguishes "the file was not read" from "no key was configured".
    #:
    #: A missing directory is harmless. pydantic-settings emits a `UserWarning` and
    #: falls back to the environment, so a development machine without `/run/secrets`
    #: is unaffected, and so are the integration tests.
    model_config = SettingsConfigDict(
        env_prefix="ESC_",
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        secrets_dir="/run/secrets",
        extra="ignore",
    )

    environment: Literal["development", "testing", "production"] = "development"

    api_key: str | None = None

    base_url: str = Field(
        default="",
        description=(
            "Overrides the URL derived from `environment`. Set `ESC_BASE_URL` to point "
            "at a local mock or a router deployment that is not one of the three known "
            "ones; leave it unset otherwise."
        ),
    )

    timeout: float = Field(
        default=10.0,
        gt=0,
        description=(
            "Seconds before a single request is given up on. The default is generous "
            "because `generate-escn` and the paged list endpoints are noticeably slower "
            "than the rest of the API."
        ),
    )

    verify_https: bool = Field(
        default=True,
        description="Only ever set to false against a local mock with a self-signed certificate.",
    )

    @model_validator(mode="after")
    def _derive_base_url(self) -> "Settings":
        """Fill `base_url` from `environment` unless it was set explicitly.

        Done here rather than in a property so that the resolved URL is part of the
        model: it shows up in `model_dump()`, in logs and in a `--help` dump, which is
        exactly where somebody looks when the client talked to the wrong deployment.
        """
        if not self.base_url:
            # `object.__setattr__` is not needed -- the model is mutable by default --
            # but assigning inside an `after` validator would re-run validation, so the
            # private attribute is set directly on `__dict__`.
            self.__dict__["base_url"] = BASE_URLS[self.environment]
        return self
