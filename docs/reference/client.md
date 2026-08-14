# Client

```{eval-rst}
.. autoclass:: edutap.esc_router_api.client.ESCRouterClient
   :members:
   :special-members: __init__

.. autofunction:: edutap.esc_router_api.client.get_default_client

.. autofunction:: edutap.esc_router_api.client.set_default_client

.. autofunction:: edutap.esc_router_api.client.close_default_client

.. autodata:: edutap.esc_router_api.client.PAGE_SIZE
```

## The module-level functions

`edutap.esc_router_api.api` mirrors every method above as a plain function against the
process-wide client. Use it in a script; use the class in anything that manages its own
connection pool. See [Share one client across an application](../howto/share-a-client.md).

```{eval-rst}
.. automodule:: edutap.esc_router_api.api
   :members:
```
