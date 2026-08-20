# Contributing

## Get set up

```console
git clone git@github.com:edutap-eu/edutap.esc_router_api.git
cd edutap.esc_router_api
make venv
prek install     # or: pre-commit install
```

`make help` lists everything else.

## Before you open a pull request

```console
make lint         # ruff check, ruff format --check, ty check
make test-local   # the unit suite -- no network
make docs         # sphinx-build -W, warnings are errors
```

CI runs the same Make targets. That is deliberate: a job that restates the commands drifts
from them, and it drifts silently, because nobody reads two files side by side.

## Working practice

Branch first — `feature/…`, `fix/…`, `chore/…`, `docs/…`. Never commit on `main`; it takes
a pull request with a review.

[Conventional Commits](https://www.conventionalcommits.org/). Pull request descriptions
carry a summary, what was tested, and the risks.

Everything is written in **English** — including commit messages and review replies, and
including in a conversation held in another language. See [CLAUDE.md](CLAUDE.md), which is
the full set of rules for this repository and applies to people as much as to agents.

## Changing the API surface

The router's OpenAPI document is the source of truth and lives at
`tests/data/esc-router-v2.json`.

```console
make refresh-spec
make test-local
```

Two tests will tell you what moved: `test_models_match_spec.py` on fields, required flags
and deprecations, `test_check_api_coverage.py` on operations. **Do not weaken either to
make a change land.** They exist because the models had drifted two revisions behind the
router with nothing to say so.

Read the diff on the JSON before fixing the failures. Occasionally the answer is that the
router is mid-deployment rather than that it changed.

## Writing tests

Unit tests drive the real `ESCRouterClient` over an `httpx2.MockTransport` — see
`tests/conftest.py`. Do not mock the client itself; that tests the test.

Anything needing a live router goes in `tests/integration/`, carries the `integration`
marker, and runs only under `--run-integration`. It must create what it needs and clean up
after itself: the sandbox is shared, and an earlier version of that suite finished by
deleting every person on the router.

## Documentation

Sphinx and MyST under `docs/`, arranged by [Diátaxis](https://diataxis.fr):

| Directory | For |
| --- | --- |
| `tutorial/` | Somebody who has not done this before, learning by doing it. |
| `howto/` | Somebody with a specific job to get done. |
| `reference/` | Looking something up. Mostly generated from docstrings. |
| `explanation/` | Understanding why something is the way it is. |
| `adr/` | One architecture decision each, never rewritten. |
| `superpowers/` | Working documents. Excluded from the published build. |

An ADR is written only when all three hold: the decision is hard to reverse, it is
surprising without its context, and it came out of a real trade-off. A changed decision
gets a new ADR that supersedes the old one; the old one stays as it was.

## Releases

See [RELEASING.md](RELEASING.md). The short version: the version comes from the git tag,
every merge to `main` publishes to test.pypi.org, and a GitHub Release publishes to
pypi.org.
