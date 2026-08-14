# Settings

Configuration comes from the environment, prefixed `ESC_`, and from a `.env` file in the
working directory. Nothing is read at import time -- the values are resolved when a
`Settings` instance is built, which is when `ESCRouterClient.from_settings()` runs.

| Variable | Default | What it does |
| --- | --- | --- |
| `ESC_API_KEY` | unset | Sent as `Authorization: Bearer …`. Required for everything but the public card status. |
| `ESC_ENVIRONMENT` | `development` | `development`, `testing` or `production`. Chooses the base URL. |
| `ESC_BASE_URL` | derived | Overrides the URL derived from the environment. For a local mock or an unlisted deployment. |
| `ESC_TIMEOUT` | `10.0` | Seconds per request. Must be greater than zero. |
| `ESC_VERIFY_HTTPS` | `true` | Only ever false against a local mock with a self-signed certificate. |

The default is the **sandbox**, not production. A deployment that forgets to set
`ESC_ENVIRONMENT` talks to a test register rather than to a live one.

```{eval-rst}
.. autoclass:: edutap.esc_router_api.settings.Settings
   :members:

.. autodata:: edutap.esc_router_api.settings.BASE_URLS
```
