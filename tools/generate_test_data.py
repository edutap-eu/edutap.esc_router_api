"""Regenerate `tests/data/persons.csv`, the sample cohort for the integration tests.

Not a test and not collected as one -- it writes a fixture, so it runs when somebody
asks it to and never as a side effect of `pytest`. Needs the `dev` dependency group,
which carries faker for this one script.

    .venv/bin/python tools/generate_test_data.py
"""

import csv
import pathlib
import random

from faker import Faker


# The script lives in tools/ and the fixture lives in tests/data/, so the path goes up
# one level. It used to be `__file__.parent / "data"`, which was right while the script
# sat in tests/ and silently wrong the moment it moved.
DATA_DIR = pathlib.Path(__file__).resolve().parent.parent / "tests" / "data"


def generate_save_email(first_name, last_name, domain="campus.lmu.de"):
    """Fold accents and umlauts out of a name so it can serve as a local part."""
    email = f"{first_name.lower()}.{last_name.lower()}@{domain}"
    email = (
        email.replace("ä", "ae")
        .replace("ö", "oe")
        .replace("ü", "ue")
        .replace("ß", "ss")
        .replace("á", "a")
        .replace("à", "a")
        .replace("â", "a")
        .replace("ã", "a")
        .replace("å", "a")
        .replace("é", "e")
        .replace("è", "e")
        .replace("ê", "e")
        .replace("ë", "e")
        .replace("í", "i")
        .replace("ì", "i")
        .replace("î", "i")
        .replace("ï", "i")
        .replace("ó", "o")
        .replace("ò", "o")
        .replace("ô", "o")
        .replace("õ", "o")
        .replace("ö", "oe")
        .replace("ú", "u")
        .replace("ù", "u")
        .replace("û", "u")
        .replace("ü", "ue")
        .replace("ç", "c")
        .replace("ñ", "n")
        .replace(" ", "")
    )
    return email


def generate_fake_person_data(locale):
    """Invent one person: name, address-safe email, ESI and phone number."""
    fake = Faker(locale=locale)
    # Test data, not a secret: `random` is the right tool and `secrets` would be
    # theatre. The linter's blanket warning about pseudo-random generators is noted
    # and dismissed here rather than repo-wide.
    fake.seed_instance(random.randint(1, 99999))  # noqa: S311

    first_name = fake.first_name()
    last_name = fake.last_name()
    email = fake.email(domain="testcampus.lmu.de")
    # email = generate_save_email(first_name.lower(), last_name.lower(), "@testcampus.lmu.de")

    matrikelnummer = fake.random_int(min=10000000, max=99999999)
    esi = f"urn:schac:personalUniqueCode:int:esi:lmu.de:{matrikelnummer}"
    fake = Faker("de_DE")
    phone = fake.phone_number()
    # email = fake.email(domain="testcampus.lmu.de")

    return {
        "name": f"{first_name} {last_name}",
        "email": email,
        "esi": esi,
        "phone": phone,
    }


def main():
    """Write a cohort spread across the locales below into tests/data/persons.csv."""
    locales = {
        "de_DE": 100,
        "de_AT": 20,
        "de_CH": 10,
        "en_GB": 5,
        "en_US": 15,
        "es_ES": 5,
        "pt_PT": 5,
        "pt_BR": 5,
        "fr_FR": 5,
        "it_IT": 20,
        "ja_JP": 5,
        "ko_KR": 5,
        "zh_CN": 5,
    }

    persons = []

    for locale, number in locales.items():
        for _ in range(number):
            person_data = generate_fake_person_data(locale)
            persons.append(person_data)
            print(person_data)

    with open(DATA_DIR / "persons.csv", mode="w", encoding="utf-8") as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=person_data.keys())
        writer.writeheader()
        writer.writerows(persons)


if __name__ == "__main__":
    main()
