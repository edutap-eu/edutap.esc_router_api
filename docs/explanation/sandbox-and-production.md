# Sandbox and production

The router has three deployments as far as this package is concerned, and `ESC_ENVIRONMENT`
picks between them.

| `ESC_ENVIRONMENT` | Base URL |
| --- | --- |
| `development` (default) | `https://sandbox.europeanstudentcard.eu/esc-rest/` |
| `testing` | `https://sandbox.europeanstudentcard.eu/esc-rest/` |
| `production` | `https://router.europeanstudentcard.eu/esc-rest/` |

## The default is the sandbox, deliberately

An unset variable is the commonest configuration mistake there is, and the cost of
guessing wrong is not symmetric. Guessing "sandbox" when production was meant produces a
call that fails or writes to a test register. Guessing "production" when the sandbox was
meant writes to a live student register. So the default is the one whose failure mode is
recoverable.

## Production is not reachable from everywhere

The production router answers **403 to any address that is not whitelisted**. That is
worth knowing because of how it presents: a deployment on the wrong network gets an
authorisation failure, not a connection error, and the natural reaction is to go looking
for a bad API key.

Measured on 2026-08-14: an anonymous request to the production OpenAPI document from
outside answered 403, while the sandbox and development hosts answered 200 with
byte-identical documents. That is what they did on the day we looked -- not a guarantee
about what they serve tomorrow.

## They are the same API

Sandbox and production expose the same V2 surface. The specification in
`tests/data/esc-router-v2.json` is fetched from the sandbox for that reason, and
[Refresh the OpenAPI specification](../howto/refresh-the-specification.md) shows how to
diff it against production if you have access.

What differs is the data. The sandbox is shared between institutions, its records are
disposable, and nothing in it should be treated as a fixture that will still be there
tomorrow.
