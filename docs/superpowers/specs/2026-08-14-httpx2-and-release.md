# httpx2, an injected client, and a release path

**Date**: 2026-08-14
**Status**: implemented

A snapshot of what was decided and what was found on that date. Not maintained.

## What prompted it

The package worked but had stopped moving with anything around it: black, isort, flake8
and mypy; `httpx`; a static version; no documentation; no release automation. Meanwhile
the other eduTAP packages — `edutap.data_models`, `edutap.observability_settings`,
`edutap.wallet_google`, `terminal_status_panel` — had settled on uv, ruff, ty, `httpx2`
and a two-stage publish to test.pypi.org and pypi.org.

The trigger was a request to bring it in line with those and to check it against a current
OpenAPI specification.

## What the specification comparison found

The attached specification turned out to be **identical** to what
`https://dev.europeanstudentcard.eu/esc-rest/v3/api-docs/V2` and
`https://sandbox.europeanstudentcard.eu/esc-rest/v3/api-docs/V2` served that day — 18
operations, 20 schemas, byte-identical documents. Production answered 403 to an anonymous
request, so it could not be compared directly. *(Measured 2026-08-14.)*

Against the repository's last capture:

- Added: `getCsvConfig`, `validateCsv`, schema `CsvValidationError`.
- Removed: `issueCard` and `IssueResponseView` — an operation this package implemented and
  was calling into nothing.
- Removed fields: `CardLiteView.cardStatusType`, `OrganisationLiteView.qrColor`.

Against `models.py`, which was a further revision behind: `AddressView` had been replaced
wholesale, `PointView` and `CsvValidationError` were missing, `PersonOrganisationView` had
gained `fullName` and `hasPicture`, `PersonOrganisationUpdateView` carried `fax` and
`phone` that the router does not have, and `fullName` was required here while the router
had made it optional and deprecated it.

That last one is the substantive change: **`fullName` moved from the person to the
person-organisation relation.** A name belongs to an enrolment.

## Defects found on the way

Not the subject of the work, but found by doing it:

1. The three picture operations interpolated the builtin `id` into the URL — there was no
   organisation parameter at all. Every request went to a path containing `<built-in
   function id>`. They had never worked.
2. `add_person_image` posted raw bytes where the router wants `multipart/form-data`, and
   checked for 204 where it answers 201.
3. Both pagination loops contained `elif len(result) < len(result) + 10 <= size`, and no
   two of their exit conditions agreed.
4. `SessionManager._cleanup_client` called `aclose()` without awaiting it, and registered
   an `atexit` hook per client creation.
5. `logging.config.dictConfig()` ran at import time, reconfiguring the importing
   application's logging.
6. `load_dotenv()` at import, with `python-dotenv` undeclared as a dependency.
7. `print()` in fourteen places.
8. `assert` used for validation in `generate_ESI`, so absent under `python -O`.
9. `cardNumber: UUID4 | str` — an ESCN is a version *1* UUID, so the `UUID4` branch failed
   on every real value and fell through to `str`.
10. No `__init__.py`, no `py.typed`.
11. Every test needed the network, and the specification check *overwrote its own
    fixtures* while running.

## Decisions

Taken with the repository owner before implementation:

| Question | Decision |
| --- | --- |
| Python floor | `>=3.13`, matching `edutap.data_models`. 3.10 reaches end of life 2026-10-31. |
| API shape | `ESCRouterClient` with an injected `httpx2.AsyncClient`, module-level functions kept as a facade. |
| GitHub org | `edutap-eu` — the existing remote. |
| Documentation | Sphinx + MyST under `docs/`, arranged by Diátaxis. |

The client decision is recorded properly in
[`docs/adr/0001-httpx2-and-an-injected-client.md`](../../adr/0001-httpx2-and-an-injected-client.md).

Version chosen: **0.1.0**. A 1.0.0b1 was proposed and rejected by the repository owner in
favour of a 0.x line, which matches the sibling packages -- `edutap.data_models` is on
0.2.x and `edutap.observability_settings` on 0.1.3, both with `Development Status :: 4 -
Beta`. A 0.x also states the thing that is true: the shape is still moving.

`hatch-vcs` rather than a static version, because the release workflow uploads to
test.pypi.org on every merge and test.pypi refuses a repeated version.

## Left undone, deliberately

**Dates stay `str`.** `issuedAt` and `expiresAt` are ISO-8601 `yyyy-MM-dd` and would be
better as `datetime.date`. It changes what `model_dump()` returns for every caller, and
this release already moves `fullName`. One breaking change at a time.

**Two things only the repository owner can do**, written up in `RELEASING.md`: create the
`release-test-pypi` and `release-pypi` GitHub environments, and register the pending
trusted publishers on both indexes. The repository also has **no git tag yet**, so until
one exists every build is `0.1.devN`.

**Production was never called.** The specification, the models and the integration tests
are all against the sandbox. If production has drifted from it, that surfaces only when
somebody with access runs the integration suite there — which the suite itself refuses to
do, on purpose.
