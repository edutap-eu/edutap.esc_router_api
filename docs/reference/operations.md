# Operation table

Every operation the ESC Router V2 API publishes, and what implements it here. The table
is complete in both directions, and `tests/test_check_api_coverage.py` keeps it that
way -- an operation the router adds or withdraws fails that test rather than going
unnoticed.

All paths are relative to the router base URL, which already ends in `/esc-rest`.

## Persons

| Operation | Router | Client method | Module function |
| --- | --- | --- | --- |
| `findAll` | `GET /api/v2/persons` | `list_persons` | `api.list_persons` |
| `create` | `POST /api/v2/persons` | `add_person` | `api.add_person` |
| `findByExternalId` | `GET /api/v2/persons/{esi}` | `get_person` | `api.get_person` |
| `update` | `PUT /api/v2/persons/{esi}` | `update_person` | `api.update_person` |
| `delete` | `DELETE /api/v2/persons/{esi}` | `delete_person` | `api.delete_person` |

## Person pictures

One picture per person per organisation, so all three take the organisation identifier.

| Operation | Router | Client method | Module function |
| --- | --- | --- | --- |
| `getStudentPicture` | `GET /api/v2/organisations/{id}/person/{esi}/picture` | `get_person_image` | `api.get_person_image` |
| `uploadStudentPicture` | `POST /api/v2/organisations/{id}/person/{esi}/picture` | `add_person_image` | `api.add_person_image` |
| `deleteStudentPicture` | `DELETE /api/v2/organisations/{id}/person/{esi}/picture` | `delete_person_image` | `api.delete_person_image` |

## Cards

| Operation | Router | Client method | Module function |
| --- | --- | --- | --- |
| `findAll_1` | `GET /api/v2/cards` | `list_cards` | `api.list_cards` |
| `create_1` | `POST /api/v2/cards` | `add_card` | `api.add_card` |
| `findByExternalId_1` | `GET /api/v2/cards/{escn}` | `get_card` | `api.get_card` |
| `update_1` | `PUT /api/v2/cards/{escn}` | `update_card` | `api.update_card` |
| `delete_1` | `DELETE /api/v2/cards/{escn}` | `delete_card` | `api.delete_card` |
| `status` | `GET /api/v2/cards/{escn}/status` | `get_card_status` | `api.get_card_status` |
| `getQRCode` | `GET /api/v2/cards/{escn}/qr` | `get_card_qr_code` | `api.get_card_qr_code` |
| `getEscnList` | `GET /api/v2/cards/generate-escn` | `generate_card_numbers` | `api.generate_card_numbers` |

`status` is the only operation the router serves without an API key, and the client omits
the `Authorization` header for it accordingly.

## Bulk card import

| Operation | Router | Client method | Module function |
| --- | --- | --- | --- |
| `getCsvConfig` | `GET /api/v2/cards/csv-config` | `get_csv_config` | `api.get_csv_config` |
| `validateCsv` | `POST /api/v2/cards/validate-csv` | `validate_csv` | `api.validate_csv` |

## Withdrawn

| Operation | Router | Note |
| --- | --- | --- |
| `issueCard` | `POST /api/v2/cards/issue/{escn}/{kid}` | Removed from the router. Implemented here until 0.1.0, where it was calling an endpoint that no longer existed. |

The V1 API (`/api/v1/students`, `/api/v1/cards`) is not implemented and will not be. It
was superseded by V2 and the person model changed with it.
