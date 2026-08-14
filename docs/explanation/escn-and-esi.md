# ESCN and ESI

The two identifiers this package deals in are not opaque strings. Both encode something,
and knowing what saves a lot of guessing when a router call is rejected.

## ESCN -- the card number

A European Student Card Number is an **RFC 4122 version 1 UUID**. Not version 4: version 1
is the one built from a timestamp, a clock sequence and a *node*, and the node is where
the ESC scheme puts the card's origin.

Print one and read the last twelve hexadecimal digits:

```
25539be8-6423-103e-add8-988999978433
                        └──┬──┘└──┬──┘
                      prefix     PIC
```

`001` is the three-digit prefix that distinguishes several issuing servers of one
institution. `999978433` is the institution's nine-digit **Participant Identification
Code**, the same PIC the European Commission uses to identify a participating
organisation. A card number therefore says which institution issued it without a lookup,
which is what lets an offline verifier do something useful.

That is why `generate_ESCN()` contains a line that looks like a bug:

```python
node = int(f"{prefix:03d}{pic}", 16)
```

Reading a decimal string as hexadecimal is exactly the trick. Twelve hexadecimal digits
are exactly the 48 bits a UUID node field holds, so nothing is truncated, and formatting
the UUID puts those twelve digits back out unchanged. Converting them as decimal would
put a different, meaningless number in the node and the PIC would not be readable in the
result.

### Minted here versus reserved by the router

`generate_ESCN()` produces a valid number offline, at any rate, without a network call.
The router has never heard of it until a card is created carrying it.

`generate_card_numbers()` asks the router for numbers, at most a hundred per call, and
those come back reserved. Use it when numbers have to be printed, embossed or handed to a
card bureau before the card records exist.

## ESI -- the student identifier

A European Student Identifier is a SCHAC personal unique code:

```
urn:schac:personalUniqueCode:int:esi:<scope>:<student code>
```

The prefix is fixed -- it is a registry entry, not a convention this project chose. What
varies is the scope, and **which scope applies is a property of the country, not a
preference**:

- Where the country issues a national student number, the identifier is scoped to the
  country: `…:esi:DE:12345`. It stays the same when the student moves between
  institutions, which is the whole point.
- Where it does not, the identifier is scoped to the institution's SCHAC home
  organisation: `…:esi:lmu.de:12345`. A move produces a new one, and the two records are
  unrelated as far as the router is concerned.

Germany falls in the second group, which is why the examples in this documentation use
`HEI-wide-scope` with `lmu.de`.

The router rejects an identifier longer than 255 characters, so `generate_ESI()` checks
that before the request goes out.

### The old format

You will still find `CN-PIC-STUDENTCODE` in the router's own API descriptions. It is the
pre-SCHAC form and this package does not produce it. Existing records carrying it keep
working; new ones should use the format above.

## Why `cardNumber` is a `str` and not a `UUID`

Because the specification says string, and because typing it as pydantic's `UUID4` --
which this package did until 0.1.0 -- was worse than useless. An ESCN is version *1*,
so every real card number failed that branch of the union and fell through to `str`
anyway. The annotation described something that never happened.

Where you want a UUID, say so:

```python
number = uuid.UUID(card.cardNumber)
assert number.version == 1
```
