# Run the integration tests

`make test-local` never opens a socket. The tests that talk to a real ESC Router are held
back behind a marker, so a plain `pytest` run cannot reach the network by accident and CI
does not depend on a router being up.

```console
export ESC_API_KEY="your-sandbox-key"
make test-integration
```

That expands to `pytest --run-integration -m integration`. Both halves are needed:
`--run-integration` is what enables them, and `-m integration` narrows the run to only
them. `-m integration` on its own reports them as skipped, which reads like a pass.

## The guards

The suite refuses to run in two situations, and skips rather than fails in both -- an
unconfigured machine is not a defect.

**No `ESC_API_KEY`.** Nothing to authenticate with.

**`ESC_ENVIRONMENT=production`.** These tests create and delete persons and cards.
Against production those are real students. Unset the variable or set it to
`development`.

## What they do to the sandbox

Each test creates what it needs with a fresh UUID as the student code, asserts against
that, and deletes it afterwards. Two runs at once, or two developers, do not collide.

The sandbox is shared, so nothing here deletes anything it did not create. An earlier
version of this suite finished by deleting every person on the router, which worked
exactly once.

## Reading a failure

An `ESCRouterAuthenticationError` is usually a key that is valid but not authorised for
the PIC in the request rather than an expired key -- the router uses 401 for both. Check
which organisation your key belongs to before reissuing it.
