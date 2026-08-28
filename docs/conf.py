"""Sphinx configuration for edutap.esc_router_api.

English, like the rest of this repository: the package belongs to eduTAP proper rather
than to any single institution.
"""

# ---------------------------------------------------------------------------
# Project
# ---------------------------------------------------------------------------

project = "edutap.esc_router_api"
author = "eduTAP"
copyright = "eduTAP"  # noqa: A001  (Sphinx names this variable, we do not)
language = "en"

# ---------------------------------------------------------------------------
# Extensions
# ---------------------------------------------------------------------------

extensions = [
    "myst_parser",
    "sphinx.ext.autodoc",
    "sphinx.ext.intersphinx",
    "sphinx.ext.napoleon",
    "sphinx_copybutton",
    "sphinx_design",
]

myst_enable_extensions = [
    "attrs_block",
    "attrs_inline",
    "colon_fence",
    "deflist",
    "substitution",
]

# `linkify` is deliberately NOT enabled. It turns any bare token that looks like a host
# into a link -- `README.md` in prose became `http://README.md`, and a domain used as an
# example, which this documentation is full of, became a link nobody wrote. Autolinks
# written as <https://example.org> work without it.

# Heading anchors up to level three, so `page.md#a-heading` resolves.
myst_heading_anchors = 3

# ---------------------------------------------------------------------------
# API reference
# ---------------------------------------------------------------------------

autodoc_member_order = "bysource"
autodoc_typehints = "description"
autodoc_default_options = {
    "members": True,
    "undoc-members": False,
    "show-inheritance": True,
}

# `pydantic` and `httpx2` types appear in signatures. Without the inventories they
# render as unlinked text, and a reader chasing `httpx2.AsyncClient` has nowhere to go.
intersphinx_mapping = {
    "python": ("https://docs.python.org/3", None),
    "pydantic": ("https://docs.pydantic.dev/latest", None),
}

# ---------------------------------------------------------------------------
# Sources
# ---------------------------------------------------------------------------

exclude_patterns = [
    "_build",
    ".venv",
    # Design records of past working sessions. They stay in the repository and are
    # readable there, but they document a decision at a point in time, not the current
    # state -- publishing them would offer them as guidance they are not.
    "superpowers",
    "Thumbs.db",
    ".DS_Store",
]

# ---------------------------------------------------------------------------
# HTML output
# ---------------------------------------------------------------------------

html_theme = "pydata_sphinx_theme"
html_title = "edutap.esc_router_api"

html_theme_options = {
    "show_toc_level": 2,
    "navigation_with_keys": True,
    "icon_links": [
        {
            "name": "GitHub",
            "url": "https://github.com/edutap-eu/edutap.esc_router_api",
            "icon": "fa-brands fa-github",
            "type": "fontawesome",
        },
    ],
    "footer_start": ["copyright"],
    "footer_end": ["last-updated"],
}

html_last_updated_fmt = "%Y-%m-%d"

# ---------------------------------------------------------------------------
# linkcheck
# ---------------------------------------------------------------------------

linkcheck_ignore = [
    # The production router answers 403 where the sandbox answers 200, so
    # linkcheck can only ever report a false failure here.
    r"https://router\.europeanstudentcard\.eu.*",
    # Hosts that exist only while a local mock runs.
    r"https?://localhost.*",
    r"https?://127\.0\.0\.1.*",
    r"https?://router\.test.*",
]

# GitHub builds its `#L42` line anchors in the browser, so they are never in the HTML
# linkcheck downloads. Checking them would report every source link as broken; the URL
# itself is still verified.
linkcheck_anchors_ignore_for_url = [
    r"https://github\.com/.*",
]
