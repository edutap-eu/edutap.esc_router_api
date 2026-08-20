# 1. httpx2 and an injected HTTP client

- **Status**: accepted
- **Date**: 2026-08-14

## Context

The package talked to the router through a module-level `SessionManager` holding a
thread-local `httpx.AsyncClient`, created lazily and registered with `atexit` for cleanup.
Every API function reached for `session_manager.client` and repeated the same
sixteen-branch `match` on the status code.

Three problems came out of that arrangement rather than out of any single line in it.

**Nothing could be tested without the network.** There was no seam to inject a transport
through, so every test in the suite -- including the one that checked the specification
was up to date -- opened a socket to the sandbox router. CI could therefore never be green
on its own terms, and the suite could not run on a laptop on a train.

**A second connection pool.** Every service in this estate that would use the package
already keeps one `httpx.AsyncClient` for its outbound calls. A private thread-local pool
inside a library duplicates the limits, the keep-alives and the TLS handshakes, and it is
invisible to whoever is tuning the ones they know about.

**Cleanup that did not run.** `_cleanup_client` called `aclose()` without awaiting it, so
the coroutine was created and discarded; `atexit.register` was called once per client
creation rather than once. Neither showed up as a failure, because a leaked pool at
interpreter exit is silent.

Separately, the eduTAP packages had settled on `httpx2` as the house HTTP client, and the
services this package is consumed by are on it.

## Decision

`ESCRouterClient` takes an `httpx2.AsyncClient` as a constructor argument. When one is not
passed it builds one and records that it owns it; `aclose()` closes the pool only in that
case.

The module-level functions in `edutap.esc_router_api.api` stay, as a thin facade over a
process-wide client built from the environment on first use, replaceable with
`set_default_client()`. The facade holds no state the class does not.

Status-code handling moves into one private `_request` method, and the exceptions it
raises are this package's own -- nothing from `httpx2` escapes.

## Consequences

The unit suite runs against `httpx2.MockTransport` and finishes in a fifth of a second
without a socket. What it exercises is the real client with the wire replaced, not a mock
of the client.

A FastAPI application shares its pool by passing it in, and is not surprised by an
`aclose()` in a dependency taking down its other outbound calls.

Callers catch `ESCRouterError` and its subclasses and never import `httpx2` to handle a
router failure. That also means the transport could be replaced again without touching
any caller.

The cost is a constructor with five keyword arguments where there used to be an import.
`ESCRouterClient.from_settings()` covers the common case in one call, and the tutorial
uses it throughout.

The process-wide client is a compromise and is worth naming as one: it is global state,
and it exists because `from …api import get_person` with no setup is what makes the
package usable from a script or a notebook. It is not thread-local, unlike its
predecessor -- an async client is safe to share across tasks, and threads were never the
axis this needed to scale on.
