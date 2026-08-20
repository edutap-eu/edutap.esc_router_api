# Refresh the OpenAPI specification

The models and the API surface are checked against a copy of the router's OpenAPI
document at `tests/data/esc-router-v2.json`. When the router changes, that copy is how
the change becomes visible.

```console
make refresh-spec
make test-local
```

The first target overwrites the file with what the sandbox router serves right now. The
second says what moved:

- `test_models_match_spec.py` fails where a field appeared, disappeared, became required,
  stopped being required, or was deprecated.
- `test_check_api_coverage.py` fails where an operation appeared or was withdrawn.

Read the diff on the JSON file before fixing the failures. The tests tell you *that*
something moved; the diff tells you *what*, and occasionally the answer is that the
router is mid-deployment rather than that it changed.

## Why the fetch is not a test

It used to be. A test downloaded three specifications and wrote them over the checked-in
fixtures, which meant a run against a router mid-deployment quietly changed what every
later run compared against -- and the suite could not run without the internet at all.
Fetching now happens when somebody asks for it, and the result lands in a diff somebody
reads.

## Why the sandbox host

`make refresh-spec` names `sandbox.europeanstudentcard.eu`. The production router answers
403 to any address that is not whitelisted, so nobody outside the allowed network could
run the target against it.

Measured on 2026-08-14: the sandbox and development hosts returned byte-identical
documents, and both matched the specification we were working from. That is what they did
on the day we looked, not a guarantee. If you have production access and want to be sure,
fetch it and diff:

```console
curl -s https://router.europeanstudentcard.eu/esc-rest/v3/api-docs/V2 \
  | python3 -c 'import json,sys; json.dump(json.load(sys.stdin), sys.stdout, indent=2, sort_keys=True); print()' \
  | diff - tests/data/esc-router-v2.json
```
