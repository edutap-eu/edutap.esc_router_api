# Upload and read a card picture

The router stores one portrait per person **per organisation**. That is why all three
picture operations take an organisation identifier as well as the student's ESI: your
institution's copy of a student's picture is not the same record as another
institution's.

## Upload

```python
image = pathlib.Path("portrait.jpg").read_bytes()

await client.add_person_image(
    organisation_id=PIC,
    esi=esi,
    image=image,
    filename="portrait.jpg",
    content_type="image/jpeg",
    resize=True,
)
```

The router wants exactly **200x300 pixels**. `resize=True` tells it to crop and scale
whatever you send; without the flag a differently sized image is refused outright. Send
`resize=False` only when you have already produced the exact dimensions and want the
router to reject anything that is not.

## Read

```python
image = await client.get_person_image(PIC, esi)
pathlib.Path("portrait.jpg").write_bytes(image)
```

The bytes come back as sent. There is no format negotiation and no variant endpoint.

## Delete

```python
await client.delete_person_image(PIC, esi)
```

## Finding out whether there is one

Reading a picture that does not exist raises `ESCRouterNotFound`, which is a wasted round
trip if you only wanted to know. The person record already says:

```python
person = await client.get_person(esi)
for relation in person.organisations or []:
    print(relation.organisation.identifier, relation.hasPicture)
```

:::{note}
These three operations did not work at all before version 0.1.0. The organisation
identifier was missing from the signatures and the builtin `id` was interpolated into the
URL in its place, so every request went to a path containing `<built-in function id>`.
The upload also sent raw bytes where the router expects `multipart/form-data`. If you
have code written against the old signatures, it was not doing what it looked like.
:::
