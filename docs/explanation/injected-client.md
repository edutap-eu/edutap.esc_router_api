# Why the HTTP client is injected

`ESCRouterClient` takes an `httpx2.AsyncClient` rather than making one. It will make one
if you do not pass it, and then it owns it -- but the injectable seam is the point, and it
buys three things.

## A shared connection pool

A service that already keeps one `httpx2.AsyncClient` for everything it talks to gets to
use it here too. Without the seam, adding this package to a FastAPI application would
open a second pool that nothing else could use, with its own limits, its own keep-alives
and its own TLS handshakes.

## Tests that never open a socket

The unit suite hands in a client wired to an `httpx2.MockTransport`. What runs is the real
client -- its URL building, its headers, its status mapping, its pagination -- with only
the wire replaced. That is a different thing from mocking `ESCRouterClient` itself, which
would test the test.

It is why the suite finishes in a fifth of a second and why CI does not need a router to
be up. The version before this one had no test that could run without the network at all.

## Ownership that is explicit

`aclose()` closes the pool **only if this instance created it**. Closing a client that was
handed in would take down the connection pool of the application that shared it.

The previous release got this wrong twice over: it registered an `atexit` hook -- once per
client creation -- that called `aclose()` without awaiting it, so the coroutine was never
run and the pool was never released. Ownership makes the question answerable instead of
guessed at.

## What is left global

`edutap.esc_router_api.api` still has a process-wide client, built from the environment on
first use, because `from …api import get_person` with no setup is genuinely convenient in
a script or a notebook. It is a thin convenience over the class and holds nothing the
class does not. `set_default_client()` replaces it; `close_default_client()` drops it.

What it is *not* is thread-local, which is what stood here before. A thread-local
`httpx2.AsyncClient` gives every thread its own pool and its own `atexit` registration,
for no benefit -- an async client is safe to share across tasks, and threads were never
the axis this needed to scale on.
