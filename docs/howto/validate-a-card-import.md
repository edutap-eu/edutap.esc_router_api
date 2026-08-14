# Validate a bulk card import

The router accepts cards in bulk as CSV, and it will check a file without importing it.
Use that check: a rejected import tells you about the first problem, the dry run tells
you about all of them, row by row.

## Ask what the columns are

```python
config = await client.get_csv_config()
# {'personIdentifier': 0, 'cardNumber': 1, ...}
```

The mapping is column name to zero-based position. Read it rather than hard-coding the
order -- the router has reordered these columns before, and a file built against a stale
order fails in a way that looks like bad data.

## Check a file

```python
errors = await client.validate_csv(
    pathlib.Path("cards.csv").read_bytes(),
    operation="CREATE",
)

for error in errors:
    print(f"row {error.rowNumber}: {error.fieldName} -- {error.errorMessage}")
```

An empty list means every row passed.

`operation` is one of `CREATE`, `UPDATE` or `DELETE`, and it changes what counts as
valid: a `DELETE` file needs only the identifying columns, a `CREATE` file needs the
dates and the card type as well.

## What the dry run does not do

Nothing is written, and nothing is reserved either. A card number that was free when you
validated can be taken by the time you import. Where you need numbers held for you, mint
them first:

```python
numbers = await client.generate_card_numbers(PIC, number_of_escn=100)
```

That is the router's own generator and the numbers come back reserved. A hundred per call
is its ceiling. `generate_ESCN()` from `edutap.esc_router_api.utils` produces valid
numbers offline, but the router has never heard of them until a card is created --
see [ESCN and ESI](../explanation/escn-and-esi.md).
