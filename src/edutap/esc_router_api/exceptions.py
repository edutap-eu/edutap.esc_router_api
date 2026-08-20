"""Exceptions this package raises.

They are named rather than letting `httpx2` types escape, so that a caller can map a
router failure onto its own response -- a FastAPI service answering 502 or 404 -- without
importing the transport library to catch it. Everything here derives from
:class:`ESCRouterError`, so one `except` clause covers the package.

The router's own error body is an `ApiErrorMessage`; where it sent one, it is parsed and
attached as :attr:`ESCRouterError.error`.
"""

from .models import ApiErrorMessage


__all__ = [
    "ESCRouterAuthenticationError",
    "ESCRouterConflict",
    "ESCRouterError",
    "ESCRouterGone",
    "ESCRouterNotFound",
    "ESCRouterPermissionError",
    "ESCRouterRequestError",
    "ESCRouterUnavailable",
    "ESCRouterValidationError",
]


class ESCRouterError(Exception):
    """Base for everything this package raises against the router."""

    def __init__(
        self,
        message: str,
        *,
        status_code: int | None = None,
        error: ApiErrorMessage | None = None,
    ) -> None:
        """Record the human-readable message plus whatever the router disclosed."""
        super().__init__(message)
        self.status_code = status_code
        self.error = error


class ESCRouterRequestError(ESCRouterError):
    """The router rejected the request as malformed -- 400."""


class ESCRouterAuthenticationError(ESCRouterError):
    """No valid API key -- 401.

    In practice this is a missing or expired `ESC_API_KEY`. The router uses the same
    status for a key that is valid but not authorised for the PIC in the request, so a
    401 is worth checking against the key's organisation before assuming it expired.
    """


class ESCRouterPermissionError(ESCRouterError):
    """The key is valid but not allowed to do this -- 403."""


class ESCRouterNotFound(ESCRouterError):
    """No such person, card or organisation -- 404."""


class ESCRouterGone(ESCRouterNotFound):
    """The person existed and was anonymised -- 410.

    Derived from :class:`ESCRouterNotFound` on purpose: to a caller that only wants to
    know whether the record can be read, "gone" and "not there" are the same answer,
    and code written before this class existed keeps working. Catch it separately where
    the difference matters -- a 410 will not become a 200 again, so retrying or
    re-creating under the same identifier is not the fix.
    """


class ESCRouterConflict(ESCRouterError):
    """The entity already exists -- 409.

    Creating a person whose European Student Identifier is already registered lands
    here. It is the ordinary answer to a re-import, not an outage.
    """


class ESCRouterValidationError(ESCRouterError):
    """The router refused the payload on its own rules -- 422 and other 4xx."""


class ESCRouterUnavailable(ESCRouterError):
    """The router could not be reached, or failed on its own account -- 5xx and timeouts.

    This is the one to answer with a 502 and a retry, rather than by changing the
    request.
    """
