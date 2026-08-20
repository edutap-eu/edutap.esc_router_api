# Unspecified behaviour

`tests/data/esc-router-v2.json` is the source of truth for this package, and two tests
hold the code to it. Some of what the code relies on is not in that document at all.

This page lists those facts and says where each one comes from, so that nobody mistakes
a measurement for a guarantee. A measurement describes what the router did on the day
somebody looked. It can change in the next deployment, without a changelog.

## What the code assumes

| Assumption | Where | What the specification says | Origin |
| --- | --- | --- | --- |
| `number_of_escn` is capped at 100 | `ESCRouterClient.generate_card_numbers` | `numberOfESCN` is an `int32` with default 1. No `maximum` appears anywhere in the document. | Unrecorded |
| The router answers 500, not 400, when that cap is exceeded | same, in the docstring | `getEscnList` declares 200, 400 and 500. It does not say which input produces which. | Measured |
| The list endpoints ignore a page size above ten | `PAGE_SIZE` | `size` is an `int32` with default 10. No `maximum`. | Measured |
| The API key travels in `Authorization: Bearer …` | `ESCRouterClient._request` | The document declares one security scheme, `api_key`, of type `apiKey`, sent as a header named `api_key`. | Measured |

Not one `maximum`, `minimum`, `maxItems` or `exclusiveMaximum` keyword occurs in the
specification. Every bound this package enforces is therefore its own.

## The authentication mismatch

This one is worth stating plainly, because the two disagree rather than merely differ in
detail.

The specification describes an `api_key` header. The package sends `Authorization:
Bearer`. The integration suite passes against the sandbox router with the header the
package sends, so the router accepts it. Whether the router also accepts the header the
document describes has never been tried.

Do not "fix" the package to match the document here without testing the change against a
real router first. The document is the authority on *what operations exist*; on this one
point it is contradicted by observation.

## Why the bounds are enforced locally anyway

An unrecorded bound is still worth keeping. `generate_card_numbers` raises `ValueError`
before the request because the router answers 500 for an oversized batch, and a 500 is
indistinguishable from a router that is simply unwell. Failing locally names the cause.

The same reasoning does not apply to inventing new bounds. If you find yourself adding a
limit that neither the specification states nor a measurement supports, it does not
belong in the package.

## When a specification revision arrives

Run `make refresh-spec`, then check this page before anything else.

If a revision states any of the four facts above, move it out of this table and into
{doc}`operations` or {doc}`client` as an ordinary documented fact, and cite the document.
If a revision contradicts one, the measurement is stale and the code is wrong.

```{seealso}
- {doc}`operations` for the operations themselves.
- {doc}`../howto/refresh-the-specification` for updating the captured document.
```
