from faker import Faker

import pytest


fake = Faker(
    {
        "de_DE": 100,
        "de_AT": 10,
        "de_CH": 10,
        "en_GB": 20,
        "en_US": 15,
        "ja_JP": 10,
    }
)
fake.seed_instance(80539)


@pytest.fixture
def person_data():
    person = fake.person_rut()
    return {
        "name": fake.name(),
        "email": fake.email(),
        "age": fake.random_int(min=18, max=30),
        "date_of_birth": fake.date_of_birth(minimum_age=18, maximum_age=30),
    }


def test_get_all_persons():
    from edutap.esc_router_api.api_v2 import list_persons

    persons = list_persons(size=5)
    assert persons is not None
    assert len(persons) >= 0
    for person in persons:
        print(person.model_dump_json(indent=2))
        assert person.fullName is not None
        assert person.identifier is not None


@pytest.mark.parametrize(
    "esi",
    [
        "urn:schac:personalUniqueCode:int:esi:lmu.de:1234567890",
    ],
)
def test_get_person(esi: str):
    from edutap.esc_router_api.api_v2 import get_person

    person = get_person(esi=esi)
    assert person is not None
    assert person.fullName is not None
    assert person.identifier == esi
    print(person.model_dump_json(indent=2))
