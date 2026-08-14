# Share one client across an application

A script can afford `async with ESCRouterClient.from_settings()` around every call. A
server cannot: that opens a TLS connection per request and throws the pool away
afterwards. Build the client once at startup instead.

## In a FastAPI application

```python
from contextlib import asynccontextmanager

import httpx2
from fastapi import Depends
from fastapi import FastAPI

from edutap.esc_router_api import ESCRouterClient
from edutap.esc_router_api import Settings


@asynccontextmanager
async def lifespan(app: FastAPI):
    settings = Settings()
    # One httpx2 client for everything this application talks to, not one per
    # dependency. `ESCRouterClient` borrows it and will not close it.
    http = httpx2.AsyncClient(http2=True)
    app.state.esc = ESCRouterClient.from_settings(settings, client=http)
    yield
    await http.aclose()


app = FastAPI(lifespan=lifespan)


def get_esc_client() -> ESCRouterClient:
    return app.state.esc


@app.get("/cards/{escn}")
async def read_card(escn: str, client: ESCRouterClient = Depends(get_esc_client)):
    return await client.get_card(escn)
```

`aclose()` on the `ESCRouterClient` is a no-op here, on purpose: it did not create the
`httpx2.AsyncClient`, so it does not get to close it. Closing a borrowed pool would take
down every other outbound call the application makes.

## Mapping router failures onto HTTP responses

Every exception the package raises derives from `ESCRouterError`, and each one already
carries the status the router sent:

```python
from fastapi import HTTPException

from edutap.esc_router_api import ESCRouterNotFound
from edutap.esc_router_api import ESCRouterUnavailable


@app.get("/cards/{escn}")
async def read_card(escn: str, client: ESCRouterClient = Depends(get_esc_client)):
    try:
        return await client.get_card(escn)
    except ESCRouterNotFound:
        raise HTTPException(status_code=404, detail="no such card")
    except ESCRouterUnavailable:
        raise HTTPException(status_code=502, detail="the ESC Router did not answer")
```

The split that matters is between the two above. `ESCRouterNotFound` and its siblings say
something about the request and will say the same thing next time; `ESCRouterUnavailable`
says the router is having a bad minute and a retry is reasonable.

## If you would rather use the module-level functions

`edutap.esc_router_api.api` builds a process-wide client from the environment on first
use. Install your own instead, once, and the functions go through it:

```python
from edutap.esc_router_api import set_default_client

set_default_client(ESCRouterClient.from_settings(client=http))
```

`close_default_client()` releases it again. It closes the client only if the package
built it -- a client you installed yourself remains yours to close.
