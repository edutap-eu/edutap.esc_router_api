from edutap.esc_router_api.api_v2 import add_person
from edutap.esc_router_api.api_v2 import get_person
from edutap.esc_router_api.api_v2 import list_persons
from edutap.esc_router_api.models_v2 import PersonOrganisationUpdateView
from edutap.esc_router_api.models_v2 import PersonUpdateView
from edutap.esc_router_api.models_v2 import PersonView

import csv
import pathlib
import pytest


DATA_DIR = pathlib.Path(__file__).parent / "data"

PIC = "999978433"  # LMU-PIC for Test Purpose


def test_get_all_persons():
    persons = list_persons(size=5)
    assert persons is not None
    assert len(persons) >= 0
    for person in persons:
        print(person.model_dump_json(indent=2))
        assert person.fullName is not None
        assert person.identifier is not None


def test_add_person():
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

            person: PersonView = add_person(data=person_update_data)
            assert person is not None
            assert person.fullName == row["name"]
            assert person.email == row["email"]
            print(person.model_dump_json(indent=2))


@pytest.mark.parametrize(
    "esi",
    [
        "urn:schac:personalUniqueCode:int:esi:lmu.de:1234567890",
    ],
)
def test_get_person(esi: str):
    person = get_person(esi=esi)
    assert person is not None
    assert person.fullName is not None
    assert person.identifier == esi
    print(person.model_dump_json(indent=2))
