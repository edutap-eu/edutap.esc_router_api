from edutap.esc_router_api.api_v2 import add_person
from edutap.esc_router_api.api_v2 import delete_person
from edutap.esc_router_api.api_v2 import get_person
from edutap.esc_router_api.api_v2 import list_persons
from edutap.esc_router_api.models_v2 import PersonOrganisationUpdateView
from edutap.esc_router_api.models_v2 import PersonUpdateView
from edutap.esc_router_api.models_v2 import PersonView

import csv
import httpx
import pathlib
import pytest


DATA_DIR = pathlib.Path(__file__).parent / "data"

PIC = "999978433"  # LMU-PIC for Test Purpose


@pytest.mark.order(1)
@pytest.mark.asyncio
async def test_empyt_get_all_persons():
    persons = await list_persons(size=0)
    assert persons is not None
    assert len(persons) == 0


@pytest.mark.order(2)
@pytest.mark.asyncio
async def test_add_person():
    with open(DATA_DIR / "persons.csv") as f:
        reader = csv.DictReader(f)
        for row in reader:
            person_update_data: PersonUpdateView = PersonUpdateView(
                fullName=row["name"],
                identifier=row["esi"],
                identifierCode="ESI",
                # identifierCode={
                #     "key": "",
                #     "label": "",
                # },
                personOrganisationUpdateViews=[
                    PersonOrganisationUpdateView(
                        organisationIdentifier=PIC,
                        email=row["email"],
                        # phone=row["phone"],
                        # academicLevel="BACHELOR",
                    )
                ],
            )
            print(person_update_data.model_dump_json(indent=2, exclude_none=True))
            try:
                person: PersonView = await add_person(data=person_update_data)
                assert person is not None
                assert person.fullName == row["name"]
                assert person.identifier == row["esi"]
                print(person.model_dump_json(indent=2))
            except httpx.HTTPError as e:
                print(f"Error adding person: {e}")
                if e.response.status_code == 409:
                    print("Person already exists")
                elif e.response.status_code == 400:
                    print("Bad request")


@pytest.mark.order(1)
@pytest.mark.asyncio
async def test_get_all_persons():
    persons = await list_persons(size=0)
    assert persons is not None
    assert len(persons) == 0
    for person in persons:
        print(person.model_dump_json(indent=2))
        assert person.fullName is not None
        assert person.identifier is not None


@pytest.mark.order(4)
@pytest.mark.asyncio
@pytest.mark.parametrize(
    "esi",
    [
        "urn:schac:personalUniqueCode:int:esi:lmu.de:1234567890",
    ],
)
async def test_get_person(esi: str):
    person = await get_person(esi=esi)
    assert person is not None
    assert person.fullName is not None
    assert person.identifier == esi
    print(person.model_dump_json(indent=2))


@pytest.mark.order(5)
@pytest.mark.asyncio
@pytest.mark.parametrize(
    "esi",
    [
        "urn:schac:personalUniqueCode:int:esi:lmu.de:1234567890",
    ],
)
async def test_delete_person(esi: str):
    await delete_person(esi=esi)
    with pytest.raises(httpx.HTTPStatusError) as exc_info:
        person = await get_person(esi=esi)
        assert person is None
        exc_info.value.response.status_code == 404


@pytest.mark.order(6)
@pytest.mark.asyncio
async def test_delete_all_persons():
    all_persons = list_persons(size=0)

    for person in all_persons:
        esi = person.identifier
        await delete_person(esi=esi)

    all_persons = list_persons(size=0)
    assert len(all_persons) == 0
