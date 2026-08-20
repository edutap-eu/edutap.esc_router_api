# Migrating to 0.1.0

This release replaces the transport, the client, the models and the test suite. Most of
it is invisible to a caller. Four changes are not.

## `fullName` moved to the enrolment

The router deprecated `fullName` on the person and put it on the person-organisation
relation. A student can be enrolled at more than one institution, under more than one
name; the name belongs to the enrolment, not to the person.

```python
# before
PersonUpdateView(
    fullName="Ada Lovelace",
    identifier=esi,
    personOrganisationUpdateViews=[
        PersonOrganisationUpdateView(organisationIdentifier=PIC),
    ],
)

# now
PersonUpdateView(
    identifier=esi,
    personOrganisationUpdateViews=[
        PersonOrganisationUpdateView(
            organisationIdentifier=PIC,
            fullName="Ada Lovelace",
        ),
    ],
)
```

`fullName` on the person still exists and is still accepted -- it is marked deprecated
here, so an IDE and the API reference say so. Reading it back:

```python
name = next(
    (relation.fullName for relation in person.organisations or [] if relation.fullName),
    person.fullName,  # the deprecated fallback, for records written before the move
)
```

`fullName` also stopped being required on `PersonUpdateView`, `PersonView` and
`PersonLiteView`. Code that asserted it was always present will now meet `None`.

## Failures raise instead of returning `None`

Every operation used to return `X | None` and log the failure. Now each one returns `X`
and raises. The `None` was never a useful signal anyway -- the code that produced it ran
`raise_for_status()` first, so the `return None` line was unreachable on any real error.

```python
# before
card = await get_card(escn)
if card is None:
    ...  # never happened; an HTTPStatusError had already been raised

# now
from edutap.esc_router_api import ESCRouterNotFound

try:
    card = await get_card(escn)
except ESCRouterNotFound:
    ...
```

The exceptions are `httpx2`-free by design, so a service maps them onto its own responses
without importing the transport library. See [Exceptions](../reference/exceptions.md).

`delete_person` and `delete_card` used to return `True`, and return nothing now. The
`False` branch was unreachable for the same reason. **This is the one change that fails
quietly**: `if await delete_person(esi):` still compiles and is now always false.

## Three picture operations that never worked

`get_person_image`, `add_person_image` and `delete_person_image` were missing the
organisation identifier entirely, and interpolated the builtin `id` into the URL in its
place -- every request went to a path containing `<built-in function id>`. The upload also
posted raw bytes where the router expects `multipart/form-data`, and checked for 204 where
the router answers 201.

All three now take the organisation first:

```python
await client.add_person_image(PIC, esi, image, resize=True)
```

There is no compatible old behaviour to preserve, because there was none.

## Renames and removals

| Before | Now |
| --- | --- |
| `edutap.esc_router_api.session` | `edutap.esc_router_api.client` and `.settings` |
| `session_manager.client` | `ESCRouterClient` / `get_default_client()` |
| `issue_card()` | gone -- the router withdrew the operation |
| `numberOfESCN=` | `number_of_escn=` |
| `Accept=` on `get_card_qr_code` | `accept=` |
| `PersonOrganisationUpdateView.phone`, `.fax` | gone -- the router has no such fields |

New: `get_csv_config()` and `validate_csv()`, which the router had gained and this package
had not.

## Python 3.13

The floor moved from 3.10 to 3.13, matching the other eduTAP packages. 3.10 reaches end of
life on 2026-10-31, so the window it bought was two months wide.

## Things that did not change

Model field names are still the router's camelCase. `Settings` still reads `ESC_*` and a
`.env` file, and still defaults to the sandbox. `generate_ESCN()` and `generate_ESI()`
keep their names and their signatures, PEP 8 notwithstanding -- they are the released API
and appear in callers we do not own.
