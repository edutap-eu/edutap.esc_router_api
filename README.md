# edutap.esc_router_api

Async Python client for the **ESC Router**, the registry behind the European Student
Card. It is where a higher education institution registers its students and the cards it
issues them, and where anybody scanning a card's QR code is sent to ask whether that card
is still valid.

Complete coverage of the router's V2 API: persons, cards, card pictures, the public status
endpoint, offline and server-side card number minting, and the bulk import dry run.

## Install

```console
pip install edutap.esc_router_api
```

Python 3.13 or newer.

## Use

```python
from edutap.esc_router_api import ESCRouterClient

async with ESCRouterClient.from_settings() as client:
    status = await client.get_card_status("25539be8-6423-103e-add8-988999978433")
    print(status.status)  # ACTIVE
```

Configuration comes from the environment, prefixed `ESC_`, or from a `.env` file:

```ini
ESC_API_KEY=your-key
# ESC_ENVIRONMENT=production   # omit and you talk to the sandbox
```

The default is the **sandbox**, not production. A deployment that forgets the variable
writes to a test register rather than to a live one.

In a service that already keeps an `httpx2.AsyncClient`, hand it in and it will be
borrowed rather than duplicated -- and not closed:

```python
client = ESCRouterClient.from_settings(client=my_shared_httpx_client)
```

There is a module-level function per operation as well, for scripts and notebooks:

```python
from edutap.esc_router_api.api import get_person

person = await get_person("urn:schac:personalUniqueCode:int:esi:lmu.de:12345")
```

## Documentation

<https://docs.edutap.eu/packages/edutap_esc_router_api/index.html>

Start with the [tutorial](docs/tutorial/first-card.md) if the router is new to you, the
[operation table](docs/reference/operations.md) if it is not, and
[migrating to 0.1.0](docs/explanation/migrating-to-0-1-0.md) if you are coming from an
earlier release -- `fullName` moved, failures raise instead of returning `None`, and three
picture operations that never worked now do.

## Develop

```console
make venv             # .venv with the package and its dev dependencies
make lint             # ruff check, ruff format --check, ty check
make test-local       # the unit suite -- no network, well under a second
make docs             # sphinx-build -W
make help             # everything else
```

The unit suite never opens a socket: it drives the real client over an
`httpx2.MockTransport`. The tests that talk to a real router are held behind a marker --
see [Run the integration tests](docs/howto/run-the-integration-tests.md).

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md). Releases are described in
[RELEASING.md](RELEASING.md).

## Licence

EUPL 1.2. See [LICENSE](LICENSE).
