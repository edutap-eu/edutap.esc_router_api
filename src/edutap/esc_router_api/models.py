from annotated_types import Ge
from annotated_types import Le
from datetime import datetime
from pydantic import BaseModel
from pydantic import EmailStr
from pydantic import UUID4
from pydantic_extra_types.phone_numbers import PhoneNumber
from typing import Annotated
from typing import List
from typing import Literal
from typing import Optional


AllowedAcademicLevel = Annotated[int, Ge(6), Le(8)]
ACADEMIC_LEVELS: Literal["BACHELOR", "MASTER", "DOCTORATE"]
AllowedCardType = Annotated[int, Ge(1), Le(4)]

# --- SCHEMA-MODELLE ---


class CodeView(BaseModel):
    key: str | None = None
    label: str | None = None


class AddressView(BaseModel):
    addressName: str | None = None
    cityName: str | None = None
    country: CodeView | None = None
    streetName: str | None = None
    subdivisionCode: str | None = None


class ContactPointView(BaseModel):
    email: str | None = None


class Link(BaseModel):
    deprecation: str | None = None
    href: str | None = None
    hreflang: str | None = None
    media: str | None = None
    name: str | None = None
    profile: str | None = None
    rel: str | None = None
    title: str | None = None
    type: str | None = None


class OrganisationLiteView(BaseModel):
    address: AddressView | None = None
    contrastColor: str | None = None
    fullLabel: str | None = None
    id: int | None = None
    identifier: str | None = None
    identifierCode: CodeView | None = None
    mainColor: str | None = None
    name: str | None = None
    newLogoAt: str | None = None
    organisationType: CodeView | None = None
    schacHomeOrganization: str | None = None
    secondaryColor: str | None = None
    status: CodeView | None = None
    website: str | None = None


class ApiErrorMessage(BaseModel):
    code: str | None = None
    message: str | None = None


class PageMetadata(BaseModel):
    number: int | None = None
    size: int | None = None
    totalElements: int | None = None
    totalPages: int | None = None


class PersonOrganisationView(BaseModel):
    academicLevel: CodeView | None = None
    contactPoint: ContactPointView | None = None
    organisation: OrganisationLiteView | None = None


class PersonLiteView(BaseModel):
    fullName: str
    identifier: str
    organisations: List[PersonOrganisationView] | None = None


class CardLiteView(BaseModel):
    cardNumber: UUID4 | str | None = None
    displayName: str | None = None
    expiresAt: str | None = None
    hasOwnerAuthorization: bool | None = None
    issuedAt: str | None = None
    issuer: OrganisationLiteView | None = None
    person: PersonLiteView | None = None
    processor: OrganisationLiteView | None = None


class CardStatusView(BaseModel):
    cardNumber: UUID4 | str | None = None
    displayName: str | None = None
    expiresAt: str | None = None
    issuedAt: str | None = None
    issuerIdentifier: str | None = None
    issuerName: str | None = None
    status: str | None = None


class CardUpdateView(BaseModel):
    cardNumber: UUID4 | str | None = None
    cardStatusType: str
    cardType: str
    displayName: str | None = None
    expiresAt: str
    issuedAt: str
    issuerIdentifier: str
    personIdentifier: str
    processorIdentifier: str | None = None


class CardView(BaseModel):
    cardNumber: UUID4 | str | None = None
    cardStatusType: CodeView | None = None
    cardType: CodeView | None = None
    displayName: str | None = None
    expiresAt: str | None = None
    hasOwnerAuthorization: bool | None = None
    issuedAt: str | None = None
    issuer: OrganisationLiteView | None = None
    person: PersonLiteView | None = None
    processor: OrganisationLiteView | None = None


class PersonOrganisationUpdateView(BaseModel):
    academicLevel: Literal["BACHELOR", "MASTER", "DOCTORATE"] | None = None
    email: str | None = None
    fax: str | None = None
    organisationIdentifier: str
    phone: PhoneNumber | str | None = None


class PersonUpdateView(BaseModel):
    fullName: str
    identifier: str
    identifierCode: str | None = None
    personOrganisationUpdateViews: List[PersonOrganisationUpdateView]


class PersonView(BaseModel):
    fullName: str
    identifier: str
    identifierCode: CodeView | None = None
    organisationCount: int | None = None
    organisations: List[PersonOrganisationView] | None = None


class PagedResourcesCardLiteView(BaseModel):
    content: List[CardLiteView] | None = None
    empty: bool | None = None
    links: List[Link] | None = None
    page: PageMetadata | None = None


class PagedResourcesPersonLiteView(BaseModel):
    content: List[PersonLiteView] | None = None
    empty: bool | None = None
    links: List[Link] | None = None
    page: PageMetadata | None = None
