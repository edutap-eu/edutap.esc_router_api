"""Pydantic models for the ESC Router V2 API.

Every class here mirrors one schema of the router's OpenAPI document, which is kept in
`tests/data/esc-router-v2.json` and refreshed with `make refresh-spec`.
`tests/test_models_match_spec.py` compares the two on every run, so a field that moves
on the server side turns into a failing test rather than into a silent `None`.

Field names stay in the router's camelCase rather than being aliased to snake_case.
The mapping would have to be maintained by hand for 20 schemas, and every error in it
would look exactly like a server change.
"""

from typing import Annotated
from typing import Literal

from pydantic import BaseModel
from pydantic import ConfigDict
from pydantic import Field


__all__ = [
    "AcademicLevel",
    "AddressView",
    "ApiErrorMessage",
    "CardLiteView",
    "CardStatusType",
    "CardStatusView",
    "CardType",
    "CardUpdateView",
    "CardView",
    "CodeView",
    "ContactPointView",
    "CsvOperation",
    "CsvValidationError",
    "Link",
    "OrganisationLiteView",
    "PageMetadata",
    "PagedResourcesCardLiteView",
    "PagedResourcesPersonLiteView",
    "PersonLiteView",
    "PersonOrganisationUpdateView",
    "PersonOrganisationView",
    "PersonUpdateView",
    "PersonView",
    "PointView",
]


# --- Vocabularies -----------------------------------------------------------------
#
# The OpenAPI document types all four of these as a plain string and lists the allowed
# values in prose. They are spelled out as `Literal` here because a caller that sends
# an unlisted value gets a 400 from the router, and finding that out at request time is
# strictly worse than finding it out at construction time. The cost is that a value
# added on the server needs a release here -- which is a minor version, and a fair
# price for the four call sites this protects.

AcademicLevel = Literal["BACHELOR", "MASTER", "DOCTORATE"]

CardStatusType = Literal["ACTIVE", "INACTIVE"]

CardType = Literal[
    "UNKNOWN",  # Unknown / none
    "PASSIVE",  # Physical passive card, no electronic component
    "SMART_NO_CDZ",  # Physical smart card, without ESC data zone
    "SMART_CDZ",  # Physical smart card, with ESC data zone
    "SMART_MAY_SP",  # Physical smart card, custom data by service providers
    "SMART_PASSIVE",  # Digital passive card, no electronic component
    "SMART_PASSIVE_EMULATION",  # Digital smart card, physical card emulation
]

CsvOperation = Literal["CREATE", "UPDATE", "DELETE"]

# The router documents these as `yyyy-MM-dd ISO-8601` and they stay `str` rather than
# becoming `datetime.date`. Parsing them is the obvious improvement and it is
# deliberately not made here: it changes what `model_dump()` returns for every existing
# caller, and this release already moves `fullName`. One breaking change at a time.
IsoDate = Annotated[str, Field(examples=["2040-12-31"])]


class ESCRouterModel(BaseModel):
    """Base for every router schema.

    Unknown fields are ignored rather than rejected. The router adds properties
    without a version bump -- `hasPicture` and `PointView` both arrived that way --
    and a client that raised on them would break on a deployment it had no say in.
    """

    model_config = ConfigDict(extra="ignore")


# --- Shared value objects ---------------------------------------------------------


class CodeView(ESCRouterModel):
    """A key with a human-readable label, the router's way of typing enumerations."""

    key: str | None = None
    label: str | None = None


class PointView(ESCRouterModel):
    """A geographic location. `x` is the longitude, `y` the latitude."""

    x: float | None = None
    y: float | None = None


class AddressView(ESCRouterModel):
    """A postal address of an organisation."""

    addressDetails: str | None = None
    cityName: str | None = None
    country: CodeView | None = None
    houseNumber: str | None = None
    label: str | None = None
    otherComments: str | None = None
    point: PointView | None = None
    province: str | None = None
    streetName: str | None = None


class ContactPointView(ESCRouterModel):
    """How to reach a person at one organisation."""

    email: str | None = None


class ApiErrorMessage(ESCRouterModel):
    """The body the router returns with any 4xx or 5xx response."""

    code: str | None = None
    message: str | None = None


class Link(ESCRouterModel):
    """One HAL link out of a paged response."""

    deprecation: str | None = None
    href: str | None = None
    hreflang: str | None = None
    media: str | None = None
    name: str | None = None
    profile: str | None = None
    rel: str | None = None
    title: str | None = None
    type: str | None = None


class PageMetadata(ESCRouterModel):
    """Where in the result set one page sits."""

    number: int | None = None
    size: int | None = None
    totalElements: int | None = None
    totalPages: int | None = None


class CsvValidationError(ESCRouterModel):
    """One complaint about one row of an uploaded CSV file."""

    errorMessage: str | None = None
    fieldName: str | None = None
    params: dict[str, str] | None = None
    rowNumber: int | None = None


# --- Organisation -----------------------------------------------------------------


class OrganisationLiteView(ESCRouterModel):
    """A higher education institution or a card processor, as the router returns it."""

    address: AddressView | None = None
    contrastColor: str | None = None
    fullLabel: str | None = None
    id: int | None = None
    identifier: str | None = None
    identifierCode: CodeView | None = None
    mainColor: str | None = None
    name: str | None = None
    newLogoAt: IsoDate | None = None
    organisationType: CodeView | None = None
    schacHomeOrganization: str | None = None
    secondaryColor: str | None = None
    status: CodeView | None = None
    website: str | None = None


# --- Person -----------------------------------------------------------------------
#
# `fullName` sits on the person-organisation relation, not on the person. The router
# moved it there and deprecated the person-level field: a name belongs to an
# enrolment at one institution, and the same person can be enrolled at several under
# different names. The deprecated fields are still accepted and still returned, so
# they are modelled -- but marked, so that a caller reading the API reference or an
# IDE tooltip is told where the name now goes.


class PersonOrganisationView(ESCRouterModel):
    """A person's relation to one organisation, as the router returns it."""

    academicLevel: CodeView | None = None
    contactPoint: ContactPointView | None = None
    fullName: str | None = None
    hasPicture: bool | None = None
    organisation: OrganisationLiteView | None = None


class PersonOrganisationUpdateView(ESCRouterModel):
    """A person's relation to one organisation, as it is written."""

    academicLevel: AcademicLevel | None = None
    email: str | None = None
    fullName: str | None = None
    organisationIdentifier: str


class PersonLiteView(ESCRouterModel):
    """A person in a list response."""

    fullName: str | None = Field(
        default=None,
        deprecated="Deprecated by the router: read the name from `organisations[].fullName`.",
    )
    identifier: str
    organisations: list[PersonOrganisationView] | None = None


class PersonView(ESCRouterModel):
    """A person as returned by the single-entity endpoints."""

    fullName: str | None = Field(
        default=None,
        deprecated="Deprecated by the router: read the name from `organisations[].fullName`.",
    )
    identifier: str
    identifierCode: CodeView | None = None
    organisationCount: int | None = None
    organisations: list[PersonOrganisationView] | None = None


class PersonUpdateView(ESCRouterModel):
    """The body of a person create or update request.

    `identifier` is the European Student Identifier. Build one with
    :func:`edutap.esc_router_api.utils.generate_ESI` rather than by hand -- the prefix
    and the scope rules are easy to get subtly wrong.
    """

    fullName: str | None = Field(
        default=None,
        deprecated=(
            "Deprecated by the router: set the name on "
            "`personOrganisationUpdateViews[].fullName` instead."
        ),
    )
    identifier: str
    identifierCode: Literal["ESI"] | None = None
    personOrganisationUpdateViews: list[PersonOrganisationUpdateView] = Field(min_length=1)


# --- Card -------------------------------------------------------------------------
#
# `cardNumber` is a `str`, not a `UUID`. An ESCN is an RFC 4122 *version 1* UUID whose
# node carries the three-digit prefix and the nine-digit PIC. Typing it as pydantic's
# `UUID4` -- as this module did before -- meant every real ESCN failed that branch of
# the union and fell through to `str` anyway, so the annotation described something
# that never happened. Use `uuid.UUID(card.cardNumber)` where a UUID is wanted.


class CardLiteView(ESCRouterModel):
    """A card in a list response."""

    cardNumber: str | None = None
    displayName: str | None = None
    expiresAt: IsoDate | None = None
    hasOwnerAuthorization: bool | None = None
    issuedAt: IsoDate | None = None
    issuer: OrganisationLiteView | None = None
    person: PersonLiteView | None = None
    processor: OrganisationLiteView | None = None


class CardView(ESCRouterModel):
    """A card as returned by the single-entity endpoints."""

    cardNumber: str | None = None
    cardStatusType: CodeView | None = None
    cardType: CodeView | None = None
    displayName: str | None = None
    expiresAt: IsoDate | None = None
    hasOwnerAuthorization: bool | None = None
    issuedAt: IsoDate | None = None
    issuer: OrganisationLiteView | None = None
    person: PersonLiteView | None = None
    processor: OrganisationLiteView | None = None


class CardStatusView(ESCRouterModel):
    """What the public status endpoint discloses about a card.

    This is the only endpoint of the router that needs no API key, which is why it
    carries the issuer's name and identifier inline instead of a nested organisation.
    """

    cardNumber: str | None = None
    displayName: str | None = None
    expiresAt: IsoDate | None = None
    issuedAt: IsoDate | None = None
    issuerIdentifier: str | None = None
    issuerName: str | None = None
    status: str | None = None


class CardUpdateView(ESCRouterModel):
    """The body of a card create or update request.

    Leave `cardNumber` unset on create and the router assigns one. To reserve numbers
    ahead of time use `generate_card_numbers()`, or mint them offline with
    :func:`edutap.esc_router_api.utils.generate_ESCN`.

    Reviving an expired card takes both a status of `ACTIVE` or `INACTIVE` *and* a new
    `expiresAt`; sending only one of the two is rejected.
    """

    cardNumber: str | None = None
    cardStatusType: CardStatusType
    cardType: CardType
    displayName: str | None = None
    expiresAt: IsoDate
    issuedAt: IsoDate
    issuerIdentifier: str
    personIdentifier: str
    processorIdentifier: str | None = None


# --- Paged responses --------------------------------------------------------------


class PagedResourcesCardLiteView(ESCRouterModel):
    """One page of cards."""

    content: list[CardLiteView] | None = None
    empty: bool | None = None
    links: list[Link] | None = None
    page: PageMetadata | None = None


class PagedResourcesPersonLiteView(ESCRouterModel):
    """One page of persons."""

    content: list[PersonLiteView] | None = None
    empty: bool | None = None
    links: list[Link] | None = None
    page: PageMetadata | None = None
