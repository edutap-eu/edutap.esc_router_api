# edutap.esc_router_api

An async Python client for the **ESC Router**, the registry behind the European Student
Card. It is where a higher education institution registers its students and the cards it
issues them, and where anybody scanning a card's QR code is sent to ask whether that card
is still valid.

The package covers the router's V2 API completely: persons, cards, card pictures, the
public status endpoint, offline and server-side card number minting, and the bulk import
dry run.

```python
from edutap.esc_router_api import ESCRouterClient

async with ESCRouterClient.from_settings() as client:
    status = await client.get_card_status("25539be8-6423-103e-add8-988999978433")
    print(status.status)  # ACTIVE
```

## Where to start

::::{grid} 1 1 2 2
:gutter: 3

:::{grid-item-card} Tutorial
:link: tutorial/index
:link-type: doc

Never used it before. Register a student, issue a card, fetch its QR code -- against the
sandbox, from an empty directory.
:::

:::{grid-item-card} How-to guides
:link: howto/index
:link-type: doc

A specific job to do: share the client in a FastAPI application, upload a portrait,
validate a card import, refresh the specification.
:::

:::{grid-item-card} Reference
:link: reference/index
:link-type: doc

What every setting, class, model and exception is. The operation table maps each router
operation to the function that implements it.
:::

:::{grid-item-card} Explanation
:link: explanation/index
:link-type: doc

Why an ESCN looks the way it does, why the HTTP client is injected, and what changed in
the release that moved `fullName`.
:::

::::

## Installation

```console
pip install edutap.esc_router_api
```

Python 3.13 or newer. The only configuration that is always needed is an API key:

```console
export ESC_API_KEY="…"
```

Without `ESC_ENVIRONMENT` the client talks to the **sandbox**, never to production. That
is deliberate: a forgotten variable should not write to a live student register.

```{toctree}
:hidden:
:maxdepth: 2

tutorial/index
howto/index
reference/index
explanation/index
```
