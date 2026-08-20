"""Async client for the European Student Card Router REST API.

The short way in::

    from edutap.esc_router_api import ESCRouterClient

    async with ESCRouterClient.from_settings() as client:
        card = await client.get_card("25539be8-6423-103e-add8-988999978433")

The router is addressed through `ESC_*` environment variables -- at minimum
`ESC_API_KEY`, and `ESC_ENVIRONMENT=production` to leave the sandbox. See
:class:`~edutap.esc_router_api.settings.Settings`.

Names re-exported here are the supported surface. Anything reached through a submodule
path may move between releases.
"""

from .client import ESCRouterClient
from .client import close_default_client
from .client import get_default_client
from .client import set_default_client
from .exceptions import ESCRouterAuthenticationError
from .exceptions import ESCRouterConflict
from .exceptions import ESCRouterError
from .exceptions import ESCRouterGone
from .exceptions import ESCRouterNotFound
from .exceptions import ESCRouterPermissionError
from .exceptions import ESCRouterRequestError
from .exceptions import ESCRouterUnavailable
from .exceptions import ESCRouterValidationError
from .settings import Settings
from .utils import generate_ESCN
from .utils import generate_ESI


try:
    # Written by hatch-vcs at build time. Absent from a source checkout that was never
    # built, which is the ordinary state of a working copy -- so the fallback is the
    # normal path here, not an error.
    from ._version import __version__
except ImportError:  # pragma: no cover
    __version__ = "0.0.0.dev0"

__all__ = [
    "ESCRouterAuthenticationError",
    "ESCRouterClient",
    "ESCRouterConflict",
    "ESCRouterError",
    "ESCRouterGone",
    "ESCRouterNotFound",
    "ESCRouterPermissionError",
    "ESCRouterRequestError",
    "ESCRouterUnavailable",
    "ESCRouterValidationError",
    "Settings",
    "__version__",
    "close_default_client",
    "generate_ESCN",
    "generate_ESI",
    "get_default_client",
    "set_default_client",
]
