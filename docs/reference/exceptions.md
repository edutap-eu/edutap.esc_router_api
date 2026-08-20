# Exceptions

Nothing from `httpx2` escapes this package. A caller maps a router failure onto its own
response without importing the transport library to catch it, and one `except
ESCRouterError` covers everything.

| Status | Exception | What it usually means |
| --- | --- | --- |
| 400 | `ESCRouterRequestError` | The request was malformed. |
| 401 | `ESCRouterAuthenticationError` | No valid key -- or a valid key not authorised for the PIC in the request. |
| 403 | `ESCRouterPermissionError` | The key is valid and not allowed to do this. |
| 404 | `ESCRouterNotFound` | No such person, card or organisation. |
| 409 | `ESCRouterConflict` | The identifier is already registered. Ordinary on a re-import. |
| 410 | `ESCRouterGone` | The person existed and was anonymised. Will not come back. |
| other 4xx | `ESCRouterValidationError` | The router refused the payload on its own rules. |
| 3xx, 5xx, timeouts, connection failures | `ESCRouterUnavailable` | Retry is reasonable. |

`ESCRouterGone` derives from `ESCRouterNotFound`, so code written before it existed keeps
working. Catch it separately where the difference matters: a 410 will not become a 200,
so retrying or re-creating under the same identifier is not the fix.

Redirects are not followed. The `Authorization` header is set per request, so httpx2 has
no way to know it should be stripped on a cross-host hop -- following one would hand the
API key to wherever the router pointed. A 3xx therefore surfaces as `ESCRouterUnavailable`
naming the location it refused.

```{eval-rst}
.. automodule:: edutap.esc_router_api.exceptions
   :members:
   :show-inheritance:
   :member-order: bysource
```
