from dotenv import load_dotenv
from httpx import Client as Session
from pydantic_settings import BaseSettings
from pydantic_settings import SettingsConfigDict
from requests.adapters import HTTPAdapter
from typing import Literal

import json
import os
import threading


load_dotenv()

_THREADLOCAL = threading.local()

# BASE_URL = "https://api-sandbox.europeanstudentcard.eu/"  # Sandbox
BASE_URL = "https://api.europeanstudentcard.eu/"  # Production --> for real data only


class HTTPRecorder(HTTPAdapter):
    """Record the HTTP requests and responses to a file."""

    def send(self, request, *args, **kwargs):
        req_record = {
            "method": request.method,
            "url": request.url,
            "headers": dict(request.headers),
            "body": json.loads(request.body.decode("utf-8")),
        }
        target_directory = os.environ.get("ESC_ROUTER_RECORD_API_CALLS_DIR")
        filename = f"{target_directory}/{request.method}-{request.url.replace('/', '_')}.REQUEST.json"
        with open(filename, "w") as fp:
            json.dump(req_record, fp, indent=4)
        response = super().send(request, *args, **kwargs)
        resp_record = {
            "status_code": response.status_code,
            "headers": dict(response.headers),
            "body": response.json(),
        }
        with open(filename.replace("REQUEST", "RESPONSE"), "w") as fp:
            json.dump(resp_record, fp, indent=4)
        return response


class Settings(BaseSettings):
    """Settings for ESC Router API.


    For more on how these settings work follow https://docs.pydantic.dev/latest/concepts/pydantic_settings/

    Any default can be overridden by setting the corresponding environment variable prefixed with `EDUTAP_WALLET_GOOGLE_`.
    If a `.env` file is present in the root directory of the project, the environment variables will be loaded from there.
    """

    model_config = SettingsConfigDict(
        env_prefix="ESC_",
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    environment: Literal["development", "production"] = "development"
    api_key: str | None = None

    @property
    def base_url(self) -> str:
        if self.environment == "production":
            return "https://router.europeanstudentcard.eu/esc-rest/"
        elif self.environment == "development":
            return "https://sandbox.europeanstudentcard.eu/esc-rest/"
        return ""


class SessionManager:
    """Manages the session to the ESC Router API and provides helper methods."""

    def _make_session(self) -> Session:
        session = Session()
        session.settings = Settings()
        if session.settings.api_key:
            session.headers.update(
                {"Authorization": f"Bearer {session.settings.api_key}"}
            )
        session.base_url = session.settings.base_url
        return session

    @property
    def session(self) -> Session:
        if getattr(_THREADLOCAL, "session", None) is None:
            _THREADLOCAL.session = self._make_session()
        return _THREADLOCAL.session  # type: ignore


session_manager = SessionManager()
