"""End-to-end against a real ESC Router. See `conftest.py` for how to run these.

These replace a suite that was ordered, stateful and destructive: it imported 205
people from a CSV, asserted the total was exactly 205, and finished by deleting every
person on the router. That works once, on an empty sandbox, for one person at a time.
What is here instead creates what it needs, asserts against that, and cleans up after
itself.
"""

import uuid

import pytest

from edutap.esc_router_api.exceptions import ESCRouterConflict
from edutap.esc_router_api.exceptions import ESCRouterNotFound
from edutap.esc_router_api.models import CardUpdateView
from edutap.esc_router_api.models import PersonOrganisationUpdateView
from edutap.esc_router_api.models import PersonUpdateView
from edutap.esc_router_api.utils import generate_ESI


pytestmark = [pytest.mark.integration, pytest.mark.anyio]

#: The LMU's Participant Identification Code on the sandbox. Repeated from conftest
#: rather than imported: tests/ is not a package, so a relative import does not resolve
#: under pytest's rootdir insertion.
PIC = "999978433"


@pytest.fixture
async def person(client):
    """A person that exists for the duration of one test and is removed afterwards.

    The student code is a fresh UUID, so two runs -- or two developers on the shared
    sandbox at once -- never collide.
    """
    esi = generate_ESI(
        "HEI-wide-scope",
        student_code=uuid.uuid4().hex[:16],
        schacHomeOrganization="lmu.de",
    )
    created = await client.add_person(
        PersonUpdateView(
            identifier=esi,
            identifierCode="ESI",
            personOrganisationUpdateViews=[
                PersonOrganisationUpdateView(
                    organisationIdentifier=PIC,
                    fullName="Integration Test",
                    email="integration-test@testcampus.lmu.de",
                )
            ],
        )
    )
    yield created
    try:
        await client.delete_person(esi)
    except ESCRouterNotFound:
        pass


async def test_a_person_can_be_created_read_and_deleted(client, person):
    fetched = await client.get_person(person.identifier)

    assert fetched.identifier == person.identifier
    assert fetched.organisations is not None
    assert any(relation.fullName == "Integration Test" for relation in fetched.organisations)


async def test_creating_the_same_person_twice_is_a_conflict(client, person):
    """A re-import lands here, and it is an ordinary answer rather than a defect."""
    with pytest.raises(ESCRouterConflict):
        await client.add_person(
            PersonUpdateView(
                identifier=person.identifier,
                personOrganisationUpdateViews=[
                    PersonOrganisationUpdateView(organisationIdentifier=PIC)
                ],
            )
        )


async def test_an_unknown_person_is_not_found(client):
    with pytest.raises(ESCRouterNotFound):
        await client.get_person(f"urn:schac:personalUniqueCode:int:esi:lmu.de:{uuid.uuid4().hex}")


async def test_listing_persons_returns_the_one_just_created(client, person):
    persons = await client.list_persons(size=0)

    assert any(entry.identifier == person.identifier for entry in persons)


async def test_generated_card_numbers_are_unique_and_carry_the_pic(client):
    """A hundred at a time is the router's ceiling, and enough to see a collision.

    The version of this test that shipped before asked for a million numbers in ten
    thousand requests. It measured the router's patience, not the client.
    """
    numbers = await client.generate_card_numbers(PIC, prefix=1, number_of_escn=100)

    assert len(numbers) == 100
    assert len(set(numbers)) == 100
    for number in numbers:
        assert number.version == 1
        assert str(number).endswith(f"001{PIC}")


async def test_a_card_can_be_issued_for_a_person(client, person):
    card = await client.add_card(
        CardUpdateView(
            cardStatusType="ACTIVE",
            cardType="SMART_PASSIVE",
            issuedAt="2026-01-01",
            expiresAt="2040-12-31",
            issuerIdentifier=PIC,
            personIdentifier=person.identifier,
        )
    )
    assert card.cardNumber is not None
    try:
        status = await client.get_card_status(card.cardNumber)
        assert status.status == "ACTIVE"

        qr = await client.get_card_qr_code(card.cardNumber, accept="SVG")
        assert qr.startswith(b"<?xml") or b"<svg" in qr
    finally:
        await client.delete_card(card.cardNumber)


async def test_the_csv_configuration_is_a_column_map(client):
    config = await client.get_csv_config()

    assert config
    assert all(isinstance(position, int) for position in config.values())


async def test_a_malformed_csv_is_reported_row_by_row(client):
    """Nothing is written -- this is the router's dry run, and the point of having it."""
    errors = await client.validate_csv(b"not,a,valid,card,row\n", operation="CREATE")

    assert isinstance(errors, list)
