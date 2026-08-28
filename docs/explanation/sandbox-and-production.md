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

## Production answers 403 where the sandbox answers 200

**What was measured**, on 2026-08-14: an anonymous request to the production OpenAPI
document answered `403`, while the sandbox and development hosts answered `200` with
byte-identical documents. That is what those hosts did on the day we looked, from where
we looked -- not a guarantee about what they serve tomorrow.

**What that means is not established.** An earlier version of this page said production
answers 403 "to any address that is not whitelisted". That was a reading of the
measurement, not something any router documentation states, and it sent at least one
reader looking for an address list to register in -- which nobody could find.

At least one other reading fits the same measurement: production may simply refuse an
**anonymous** request where the sandbox serves its specification openly. No address list
required. The observation cannot tell the two apart, because the request carried no key.

**Why it is worth knowing anyway.** However it is caused, a deployment pointed at the
wrong environment gets an *authorisation* failure rather than a connection error, and
the natural reaction is to go looking for a bad API key. If a call **with a valid key**
answers 403, that is the point to ask the router operator -- not to hunt for a
whitelist.

## They are the same API

Sandbox and production expose the same V2 surface. The specification in
`tests/data/esc-router-v2.json` is fetched from the sandbox for that reason, and
[Refresh the OpenAPI specification](../howto/refresh-the-specification.md) shows how to
diff it against production if you have access.

What differs is the data. The sandbox is shared between institutions, its records are
disposable, and nothing in it should be treated as a fixture that will still be there
tomorrow.
