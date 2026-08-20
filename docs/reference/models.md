# Models

Every class here mirrors one schema of the router's OpenAPI document. Field names keep
the router's camelCase rather than being aliased to snake_case: the mapping would have to
be maintained by hand for twenty schemas, and every mistake in it would look exactly like
a server change.

Unknown fields are ignored rather than rejected. The router adds properties without a
version bump -- `hasPicture` and `PointView` both arrived that way -- and a client that
raised on them would break on a deployment it had no say in.

```{eval-rst}
.. automodule:: edutap.esc_router_api.models
   :members:
   :member-order: bysource
```
