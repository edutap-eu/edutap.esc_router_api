# CLAUDE.md — edutap.esc_router_api

Repository-specific rules. They take precedence over the global defaults.

## Language

**English only.** This repository belongs to eduTAP proper, not to any single
institution: README, documentation, docstrings, code comments, commit messages, pull
request titles and bodies, and replies to review comments.

The language follows the repository, not the conversation. A discussion held in German
still produces English artefacts here.

## What this package is

An async client for the ESC Router's V2 REST API — the registry behind the European
Student Card. It covers the router's surface completely and adds two offline identifier
factories (`generate_ESCN`, `generate_ESI`) that would otherwise be reimplemented in every
consumer.

It is a library. It has no opinion about how a service stores anything, it holds no
schema, and it depends on nothing else in the eduTAP estate.

## Guard rails

**The specification is the source of truth, and the models follow it.** The router's
OpenAPI document lives at `tests/data/esc-router-v2.json`; `make refresh-spec` updates it.
Two tests compare the code against it — `test_models_match_spec.py` on every field,
required flag and deprecation, and `test_check_api_coverage.py` on every operation. Never
weaken either to make a change land. The reason they exist is that the models were two
revisions behind the router and nothing said so: fields that had been removed were still
required here, and a function was calling an operation the router had withdrawn.

**Four runtime dependencies, and a written reason for a fifth.** `httpx2`, `pycountry`,
`pydantic`, `pydantic-settings`. What this package pulls in, every consumer pulls in.
`phonenumbers` and `pydantic_extra_types` were dropped when the fields that needed them
left the specification — a dependency loses its reason before anybody notices it is still
there.

**No global logging configuration.** A `logging.config.dictConfig()` ran at import time
here and reconfigured the logging of whatever imported the package, httpx and httpcore
included. A library takes a logger — `logging.getLogger(__name__)` — and nothing else.

**No `print()`.** It was in fourteen places, writing API payloads to stdout in a library.

**Nothing from `httpx2` escapes.** Every failure surfaces as an `ESCRouterError`
subclass, so a caller maps a router failure onto its own response without importing the
transport library to catch it. That is also what makes the transport replaceable.

**Ownership of the HTTP client is explicit.** `aclose()` closes the pool only if this
instance created it. Closing a borrowed client would take down the connection pool of the
application that shared it. See
[`docs/adr/0001-httpx2-and-an-injected-client.md`](docs/adr/0001-httpx2-and-an-injected-client.md).

**No test may open a socket by default.** The unit suite drives the real client over an
`httpx2.MockTransport`. Anything that needs a router carries the `integration` marker and
runs only under `--run-integration`. A test that writes its own fixtures, as the
specification check used to, is not a test.

**Never point the integration tests at production.** They create and delete persons and
cards. `tests/integration/conftest.py` skips when `ESC_ENVIRONMENT` is `production`; do
not add a way around it.

**No `uv.lock`.** This is a library; pinning here would push a resolution onto every
consumer.

**Released names stay released.** `generate_ESCN`, `generate_ESI`,
`ESCN_Factory_Exception` and the `type` parameter break PEP 8 and are kept anyway — they
appear in callers we do not own, and a rename for style is a break for nothing.

## Working practice

Branch first, never commit on `main`. Push only when asked. `make lint`, `make test-local`
and `make docs` green before opening a pull request.

The version comes from the git tag through hatch-vcs. Do not add a version to
`pyproject.toml`; tag instead, and see [RELEASING.md](RELEASING.md).

Design records live under `docs/superpowers/`; architecture decisions under `docs/adr/`.
Both are records of a decision at a point in time — do not rewrite them to match a later
state, write a new one.

## Sources and confidentiality

**No vendor internals — from any vendor, not just the ones currently in play.** Neither in
files nor in commit messages.

The standard is academic: a statement counts as reliable only where it can be evidenced
from public information, with a link. Everything else was obtained either by our own
testing or through insider knowledge, and the three are not interchangeable:

* **Evidenced** — public source, linked. May stand as fact.
* **Evidenced, not citable** — obtained by a person from an access-controlled area and
  checked there; the source is recorded internally but may not be published; and the
  statement is reduced to what is not confidential. May stand as fact, with exactly that
  note.
* **Measured** — established by our own testing. May be documented, but always marked as
  such, with the date: it describes what a platform did on the day we looked, not what it
  guarantees. It can change with the next release, without notice.
* **Insider knowledge** — is not written down at all.

The router's behaviour is a running example. That production answers 403 to a
non-whitelisted address, and that sandbox and development served byte-identical
specifications on 2026-08-14, are **measured** — and are written down that way, with the
date, in `docs/explanation/sandbox-and-production.md`.
