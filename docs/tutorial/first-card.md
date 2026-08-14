# Issue your first card

By the end of this you will have registered a student with the ESC Router, issued them a
card, and downloaded the QR code that a verifier scans. Everything happens against the
**sandbox**, so nothing here touches real students.

You need Python 3.13 or newer and an API key for the sandbox router. If you do not have a
key, ask whoever administers your institution's ESC Router account for one -- there is no
self-service.

## Set up

Make an empty directory and install the package:

```console
mkdir esc-tutorial && cd esc-tutorial
python -m venv .venv
.venv/bin/pip install edutap.esc_router_api
```

Put your key in a `.env` file next to your script:

```ini
ESC_API_KEY=your-sandbox-key
```

There is no `ESC_ENVIRONMENT` line, and that is the point: the default is
`development`, which resolves to the sandbox. You will add `ESC_ENVIRONMENT=production`
only when you mean it.

## Register a student

Create `tutorial.py`:

```python
import asyncio

from edutap.esc_router_api import ESCRouterClient
from edutap.esc_router_api import generate_ESI
from edutap.esc_router_api.models import PersonOrganisationUpdateView
from edutap.esc_router_api.models import PersonUpdateView

PIC = "999978433"  # replace with your institution's PIC


async def main() -> None:
    async with ESCRouterClient.from_settings() as client:
        esi = generate_ESI(
            "HEI-wide-scope",
            student_code="tutorial-0001",
            schacHomeOrganization="lmu.de",
        )

        person = await client.add_person(
            PersonUpdateView(
                identifier=esi,
                identifierCode="ESI",
                personOrganisationUpdateViews=[
                    PersonOrganisationUpdateView(
                        organisationIdentifier=PIC,
                        fullName="Ada Lovelace",
                        email="ada@example.org",
                    )
                ],
            )
        )
        print(person.identifier)


asyncio.run(main())
```

Run it:

```console
.venv/bin/python tutorial.py
```

You should see the identifier printed back.

Two things in there are worth pausing on.

`generate_ESI` builds the **European Student Identifier**. It is not a free-form string:
it is a SCHAC personal unique code, and the scope -- country-wide or institution-wide --
is a property of the country your institution sits in, not a choice. Germany has no
national student number, so `HEI-wide-scope` with your SCHAC home organisation is right
there. See [ESCN and ESI](../explanation/escn-and-esi.md).

`fullName` sits on `PersonOrganisationUpdateView`, not on the person. A student can be
enrolled at more than one institution, under more than one name, so the name belongs to
the enrolment. There is still a `fullName` on the person itself -- it is deprecated, and
setting it does nothing useful.

Run the script a second time and you get an `ESCRouterConflict`. That is the router
telling you the identifier is already registered, which on a re-import is the expected
answer rather than a failure.

## Issue a card

Add this to `main()`, after the person exists:

```python
from edutap.esc_router_api.models import CardUpdateView

card = await client.add_card(
    CardUpdateView(
        cardStatusType="ACTIVE",
        cardType="SMART_PASSIVE",
        issuedAt="2026-01-01",
        expiresAt="2030-12-31",
        issuerIdentifier=PIC,
        personIdentifier=esi,
    )
)
print(card.cardNumber)
```

`cardNumber` was left unset, so the router minted one. What comes back is a
**European Student Card Number**: an RFC 4122 version 1 UUID whose last twelve digits are
your three-digit server prefix followed by your nine-digit PIC. Look at the printed value
and you will see your PIC in it.

## Fetch the QR code

```python
qr = await client.get_card_qr_code(card.cardNumber, size="M")
with open("card.svg", "wb") as handle:
    handle.write(qr)
```

Open `card.svg`. Scanning it takes you to the router's public status page for that card.

You can ask the same question from code, and this is the one operation that needs no API
key at all:

```python
status = await client.get_card_status(card.cardNumber)
print(status.status, status.expiresAt, status.issuerName)
```

## Clean up

```python
await client.delete_card(card.cardNumber)
await client.delete_person(esi)
```

Both return nothing. They raise if anything went wrong, so reaching the next line means
it worked.

## What next

- [Share one client across a FastAPI application](../howto/share-a-client.md) -- the
  `async with` form is right for a script and wrong for a server.
- [Reference](../reference/index.md) -- every operation, setting and model.
- [Why the client is injected](../explanation/injected-client.md).
