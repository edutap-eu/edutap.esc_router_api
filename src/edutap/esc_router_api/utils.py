"""Identifier factories and the decorator that keeps the API surface honest."""

import uuid
from collections.abc import Callable
from typing import Any
from typing import Literal
from typing import TypeVar
from typing import cast

import pycountry


__all__ = [
    "ESCN_Factory_Exception",
    "ESI_Factory_Exception",
    "generate_ESCN",
    "generate_ESI",
    "openapi_method",
]

#: Every European Student Identifier starts with this. It is a SCHAC personal unique
#: code in the `int:esi` namespace -- the registry entry, not something we chose.
ESI_PREFIX = "urn:schac:personalUniqueCode:int:esi"

#: The router rejects a longer identifier outright.
ESI_MAX_LENGTH = 255

_F = TypeVar("_F", bound=Callable[..., object])

# `ESCN_Factory_Exception`, `generate_ESCN`, `generate_ESI` and the `type` parameter
# below break PEP 8 -- CapWords in a function name, a shadowed builtin. They are kept
# as they are because they are the released API of this package and appear in callers
# we do not own; renaming them for style would break those for nothing. Should the
# pep8-naming rules ever be switched on, this is the exemption to write down.


class ESCN_Factory_Exception(Exception):
    """A card number could not be built from the given PIC and prefix."""


class ESI_Factory_Exception(Exception):
    """A student identifier could not be built from the given scope and code."""


def generate_ESCN(pic: str, prefix: int = 1) -> uuid.UUID:
    """Mint a European Student Card Number offline.

    An ESCN is an RFC 4122 **version 1** UUID whose node field carries the issuing
    server's identity, so that a card number says where it came from without a lookup:
    the last twelve hex digits of the string are literally the three-digit prefix
    followed by the nine-digit PIC.

    That is why the node is built with ``int(..., 16)`` on a decimal string, which
    looks like a bug and is not. Reading the digits as hexadecimal is what makes them
    reappear unchanged in the formatted UUID; converting them as decimal would put a
    different, meaningless number there. Twelve hex digits are exactly the 48 bits a
    UUID node field holds, so nothing is truncated.

    Numbers minted here are valid but *unknown to the router* until a card is created
    with them. Where the router should reserve them instead, use
    :meth:`~edutap.esc_router_api.client.ESCRouterClient.generate_card_numbers`.

    :param pic: The institution's nine-digit Participant Identification Code.
    :param prefix: 1..999, distinguishing several issuing servers of one institution.
    :raises ESCN_Factory_Exception: The PIC is not nine digits, or the prefix is out of
        range.
    """
    if len(pic) != 9 or not pic.isdigit():
        raise ESCN_Factory_Exception(f"PIC must be nine digits, got {pic!r}")
    if not 1 <= prefix <= 999:
        raise ESCN_Factory_Exception(f"prefix must be between 1 and 999, got {prefix}")
    node = int(f"{prefix:03d}{pic}", 16)
    return uuid.uuid1(node=node)


def generate_ESI(
    type: Literal["nation-wide-scope", "HEI-wide-scope"],
    student_code: str,
    cn: str | None = None,
    schacHomeOrganization: str | None = None,
) -> str:
    """Build a European Student Identifier.

    Which of the two scopes applies is a property of the country, not a preference.
    Where a national student number exists, the identifier is scoped to the country so
    that it stays the same across a move between institutions; where it does not, it is
    scoped to the institution's SCHAC home organisation and a move produces a new one.

    :param type: `nation-wide-scope` needs `cn`; `HEI-wide-scope` needs
        `schacHomeOrganization`.
    :param student_code: The student's unique code within that scope.
    :param cn: ISO 3166-1 alpha-2 country code of the institution.
    :param schacHomeOrganization: The institution's domain, for example `lmu.de`.
    :raises ESI_Factory_Exception: The scope and its argument do not go together, the
        country code is not an ISO 3166-1 one, or the result exceeds 255 characters.
    """
    if type == "nation-wide-scope":
        if cn is None:
            raise ESI_Factory_Exception("nation-wide-scope needs a country code")
        if cn not in {country.alpha_2 for country in pycountry.countries}:
            raise ESI_Factory_Exception(f"Invalid country code: {cn}")
        scope = cn
    elif type == "HEI-wide-scope":
        if schacHomeOrganization is None:
            raise ESI_Factory_Exception("HEI-wide-scope needs a schacHomeOrganization")
        scope = schacHomeOrganization
    else:
        raise ESI_Factory_Exception(f"Invalid scope type: {type!r}")

    esi = f"{ESI_PREFIX}:{scope}:{student_code}"
    # An `assert` stood here. Under `python -O` it is removed, so the one check that
    # kept an over-long identifier from reaching the router disappeared in exactly the
    # deployment most likely to run with optimisations on.
    if len(esi) > ESI_MAX_LENGTH:
        raise ESI_Factory_Exception(
            f"ESI exceeds the maximum length of {ESI_MAX_LENGTH} characters: {len(esi)}"
        )
    return esi


def openapi_method(
    method: Literal["GET", "POST", "DELETE", "PUT", "PATCH"],
    path: str,
    operation_id: str | None = None,
) -> Callable[[_F], _F]:
    """Record which router operation a function implements.

    The attributes it attaches are what `tests/test_check_api_coverage.py` reads to
    compare the module against the OpenAPI document. That test is the reason an
    operation removed from the router -- `issueCard` was, between two releases -- shows
    up as a failure instead of as a call that quietly 404s.
    """

    def decorator(func: _F) -> _F:
        # Written through `Any` rather than with a type-checker suppression: a function
        # object does take arbitrary attributes, the checker is right that the
        # *declared* type does not, and casting says which of the two we mean.
        target = cast(Any, func)
        target.__http_method__ = method.upper()
        target.__openapi_path__ = path
        target.__openapi_operation_id__ = operation_id
        return func

    return decorator
